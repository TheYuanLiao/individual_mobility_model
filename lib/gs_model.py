import json
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import models
import validation
import mscthesis
import saopaulo
import netherlands
import genericvalidation
import pipeline
import plots


def sweden_visits(ps, gammas, betas, run_id, scale, geotweets_path="/dbs/sweden/geotweets_v.csv"):
    results_dir = os.getcwd() + "/results"
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
                        ),
                        n_days=7 * 20,
                        daily_trips_sampling=models.NormalDistribution(mean=3.14, std=1.8),
                        geotweets_path=os.getcwd() + geotweets_path,
                    )
                )

    for f in visit_factories:
        print(f.describe())
    cfgs = pipeline.config_product(
        visit_factories=visit_factories,
        home_locations_paths=[
            os.getcwd() + "/dbs/sweden/homelocations.csv",
        ]
    )
    pipe = pipeline.Pipeline()
    pipe.prepare()

    for cfg in cfgs:
        print("RUNID", run_id)

        run_directory = "{}/{}-{}-v".format(results_dir, 'sweden', run_id)
        os.makedirs(run_directory, exist_ok=True)
        with open("{}/parameters.json".format(run_directory), 'w') as f:
            json.dump(cfg.describe(), f, indent=2)

        result = pipe.run(cfg)
        pipe.visits.to_csv(os.getcwd() + "/dbs/sweden/visits/{}-v.csv".format(run_id))
        odmfig = plots.plot_odms(
            [
                result.sparse_odms[scale],
                pipe.sampers.odm[scale]
            ],
            ['model', 'sampers'],
        )
        odmfig.savefig("{}/odms-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

        distance_metrics = result.distance_metrics[scale]
        distance_metrics.to_csv("{}/distance-metrics-{}.csv".format(run_directory, scale))

        dmfig = plots.plot_distance_metrics(distance_metrics, ['model', 'sampers'])
        dmfig.savefig("{}/distance-metrics-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

        with open("{}/results.json".format(run_directory), 'w') as f:
            json.dump(result.divergence_measure, f, indent=2)

        # matplotlib keeps state (figures in global state)
        # We don't need the figures after writing to file so close them.
        # Otherwise memory usage will be immense.
        plt.close('all')
        return result.divergence_measure


def generic_visits(ps, gammas, betas, run_id, region, scale='national'):
    results_dir = os.getcwd() + "/results"
    if region == 'saopaulo':
        zone_loader = saopaulo.zones
        odm_loader = saopaulo.odm

    if region == 'netherlands':
        zone_loader = netherlands.zones
        odm_loader = netherlands.odm

    geotweets_path = os.getcwd() + "/dbs/{}/geotweets_v.csv".format(region)

    # Remove tweets on weekends?
    only_weekday = True

    # Only run baseline, and not grid search
    only_run_baseline = False
    visit_factories = []
    for beta in betas:
        for p in ps:
            for gamma in gammas:
                visit_factories.append(
                    models.Sampler(
                        model=models.PreferentialReturn(
                            p=p,
                            gamma=gamma,
                            region_sampling=models.RegionTransitionZipf(beta=beta, zipfs=1.2)
                        ),
                        n_days=7 * 20,
                        daily_trips_sampling=models.NormalDistribution(mean=3.14, std=1.8),
                        geotweets_path="",  # We read the geotweets once instead.
                    )
                )

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
        print("RUNID", run_id)
        print(visit_factory.describe())

        run_directory = "{}/{}-{}-v".format(results_dir, region, run_id)
        os.makedirs(run_directory, exist_ok=True)
        # Save parameters
        with open("{}/parameters.json".format(run_directory), 'w') as f:
            json.dump(visit_factory.describe(), f, indent=2)

        # Calculate visits
        visits = visit_factory.sample(geotweets)

        visits_dir = os.getcwd() + "/dbs/{}/visits".format(region)
        visits_file = "{}/{}-v.csv".format(visits_dir, run_id)
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
        divergence_measure = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])

        with open("{}/results.json".format(run_directory), 'w') as f:
            json.dump({scale: divergence_measure}, f, indent=2)

        # matplotlib keeps state (figures in global state)
        # We don't need the figures after writing to file so close them.
        # Otherwise memory usage will be immense.
        plt.close('all')
        return {scale: divergence_measure}
