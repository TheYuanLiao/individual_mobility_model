import json
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np

import models
import validation
import mscthesis
import saopaulo
# import netherlands
import genericvalidation

results_dir = "./../../results"

region = "saopaulo"
zone_loader = saopaulo.zones
odm_loader = saopaulo.odm
geotweets_path = "./../../dbs/{}/geotweets.csv".format(region)

# Remove tweets on weekends?
only_weekday = True

# Only run baseline, and not grid search
only_run_baseline = False

ps = [0.3, 0.6, 0.9]
gammas = [0.2, 0.5, 0.8]
betas = [0.01, 0.04, 0.07]

visit_factories = []
for beta in betas:
    for p in ps:
        for gamma in gammas:
            visit_factories.append(
                models.Sampler(
                    model=models.PreferentialReturn(
                        p=p,
                        gamma=gamma,
                        region_sampling=models.RegionTransitionZipf(beta=beta, zipfs=1.2),
                        jump_size_sampling=models.JumpSizeTrueProb(),
                    ),
                    n_days=7 * 20,
                    daily_trips_sampling=models.NormalDistribution(mean=3.14, std=1.8),
                    geotweets_path="", # We read the geotweets once instead.
                )
            )


if __name__ == "__main__":
    print("Grid searching [{} configurations]...".format(len(visit_factories)))

    print("Loading zones...")
    zones = zone_loader()

    print("Loading odm...")
    odm = odm_loader()

    print("Calculating distances...")
    distance = genericvalidation.zone_distances(zones)
    print("Calculating distance quantiles...")
    qgrps = genericvalidation.distance_quantiles(distance)

    print("Reading and filtering geotweets...")
    geotweets = mscthesis.read_geotweets_raw(geotweets_path).set_index('userid')
    if only_weekday:
        # Only look at weekday trips
        geotweets = geotweets[(geotweets['weekday'] < 6) & (0 < geotweets['weekday'])]
    # Remove users who don't have home visit in geotweets
    home_visits = geotweets.query("label == 'home'").groupby('userid').size()
    geotweets = geotweets.loc[home_visits.index]
    # Remove users with less than 20 tweets
    tweetcount = geotweets.groupby('userid').size()
    geotweets = geotweets.drop(labels=tweetcount[tweetcount < 20].index)
    # Remove users with only one region
    regioncount = geotweets.groupby(['userid', 'region']).size().groupby('userid').size()
    geotweets = geotweets.drop(labels=regioncount[regioncount < 2].index)
    # Ensure the tweets are sorted chronologically
    geotweets = geotweets.sort_values(by=['userid', 'createdat'])

    if only_run_baseline:
        print("Calculating baseline results...")
        baseline = models.geotweets_to_visits(geotweets)
        baseline_odm = genericvalidation.visits_to_odm(baseline, zones)
        dms = validation.DistanceMetrics().compute(
            qgrps,
            [odm, baseline_odm],
            ['groundtruth', 'model'] # intentionally named model to be consistent with others
        )
        run_directory = "{}/{}-baseline".format(results_dir, region)
        os.makedirs(run_directory, exist_ok=True)
        dms.to_csv("{}/distance-metrics.csv".format(run_directory))
        exit(0)

    for visit_factory in visit_factories:
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        print()
        print()
        print("RUNID", run_id)
        print(visit_factory.describe())

        run_directory = "{}/{}-{}".format(results_dir, region, run_id)
        os.makedirs(run_directory, exist_ok=True)
        # Save parameters
        with open("{}/parameters.json".format(run_directory), 'w') as f:
            json.dump(visit_factory.describe(), f, indent=2)

        # Calculate visits
        visits = visit_factory.sample(geotweets)

        visits_dir = "./../../dbs/{}/visits".format(region)
        visits_file = "{}/{}.csv".format(visits_dir, run_id)
        print("Saving visits to csv: {}".format(visits_file))
        os.makedirs(visits_dir, exist_ok=True)
        visits.to_csv(visits_file)

        model_odm = genericvalidation.visits_to_odm(visits, zones)
        dms = validation.DistanceMetrics().compute(
            qgrps,
            [odm, model_odm],
            ['groundtruth', 'model']
        )
        dms.to_csv("{}/distance-metrics.csv".format(run_directory))

        sqrerr = np.square(np.subtract(dms['groundtruth_sum'], dms['model_sum']))
        print("MSE: {:.5e}".format(sqrerr.mean()))

        # Not sure if this helps, but might as well clear as much of unneeded state as possible
        visits = None
        model_odm = None
        dms = None

        # matplotlib keeps state (figures in global state)
        # We don't need the figures after writing to file so close them.
        # Otherwise memory usage will be immense.
        plt.close('all')
