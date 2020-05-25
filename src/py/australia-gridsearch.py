import json
import datetime
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

import models
import mscthesis
import australia

results_dir = "./../../results"

region = "australia"
geotweets_path = "./../../dbs/{}/geotweets.csv".format(region)

# Remove tweets on weekends?
only_weekday = True

# Only run baseline, and not grid search
only_run_baseline = False

ps = [0.3] # 0.6, 0.9
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


def prepare_travel_survey(hts):
    hts = hts[['WAVE', 'zone', 'WEIGHTED_TRIPS', 'WEIGHTED_TOTAL_DISTANCE']].groupby(['WAVE', 'zone']).sum()
    hts = hts.WEIGHTED_TOTAL_DISTANCE / hts.WEIGHTED_TRIPS
    hts = hts.loc['2018/19']
    return hts

def visits_to_trips(visits):
    def trip_dist(t):
        return mscthesis.haversine_distance(
            t.latitude_origin, t.longitude_origin,
            t.latitude_destination, t.longitude_destination,
        )
    print("converting to trips")
    trips = mscthesis.visit_gaps(visits)
    print("calculating distances")
    trip_dists = trips.apply(trip_dist, axis=1)
    return trip_dists

def summarize_trips_per_zone(trips, user_zone):
    trip_summaries = pd.DataFrame.from_dict(dict(
        num_trips = trips.groupby('userid').size(),
        total_distance = trips.groupby('userid').sum(),
    ))
    zone_trips = user_zone.merge(trip_summaries, on='userid')
    zone_trips = zone_trips.groupby('zone').sum()
    zone_avg_distance = zone_trips.total_distance / zone_trips.num_trips
    return zone_avg_distance

if __name__ == "__main__":
    print("Grid searching [{} configurations]...".format(len(visit_factories)))

    print("Loading zones...")
    zones = australia.validation_zones()

    print("Loading travel survey...")
    hts = australia.validation_travel_survey()

    print("Loading home locations...")
    home_locations = pd.read_csv('../../dbs/australia/homelocations.csv')
    home_locations = gpd.GeoDataFrame(
        home_locations,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(home_locations.longitude, home_locations.latitude),
    ).to_crs(zones.crs)

    zone_to_user = gpd.sjoin(home_locations, zones)[['zone', 'userid']]

    print("Prepare travel survey")
    groundtruth_avg_distance = prepare_travel_survey(hts)

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
        baseline_trips = visits_to_trips(baseline)
        baseline_avg_distance = summarize_trips_per_zone(baseline_trips, zone_to_user)
        baseline_avg_distance = baseline_avg_distance.reindex(groundtruth_avg_distance.index, fill_value=0)
        sa3_res = pd.concat([groundtruth_avg_distance, baseline_avg_distance], axis=1).rename(columns={0: 'groundtruth', 1: 'model'})
        run_directory = "{}/{}-baseline".format(results_dir, region)
        os.makedirs(run_directory, exist_ok=True)
        sa3_res.to_csv("{}/sa3-metrics.csv".format(run_directory))
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

        model_trips = visits_to_trips(visits)
        model_avg_distance = summarize_trips_per_zone(model_trips, zone_to_user)
        model_avg_distance = model_avg_distance.reindex(groundtruth_avg_distance.index, fill_value=0)
        sa3_res = pd.concat([groundtruth_avg_distance, model_avg_distance], axis=1).rename(columns={0: 'groundtruth', 1: 'model'})

        sa3_res.to_csv("{}/sa3-metrics.csv".format(run_directory))

        sqrerr = np.square(np.subtract(sa3_res['groundtruth'], sa3_res['model']))
        print("MSE: {:.5e}".format(sqrerr.mean()))

        # Not sure if this helps, but might as well clear as much of unneeded state as possible
        visits = None
        model_trips = None
        model_avg_distance = None
        sa3_res = None
        sqrerr = None

        # matplotlib keeps state (figures in global state)
        # We don't need the figures after writing to file so close them.
        # Otherwise memory usage will be immense.
        plt.close('all')
