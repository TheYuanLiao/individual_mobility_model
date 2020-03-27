import json
import datetime
import os

import pandas as pd
import geopandas as gpd

import mscthesis
import models
import validation
import plots

results_dir = "./../../results"

params = {
    "input": {
        "geotweets": "./../../dbs/sweden/geotweets.csv",
        "home_locations": "./../../dbs/sweden/homelocations.csv"
    },
    "model": {
        "p": 0.66,
        "gamma": 0.6,
        "region_sampling": {
            "name": "zipf",
            "s": 1.2,
        },
        "jump_size_sampling": {
            "name": "trueProb",
        },
    },
    "sampler": {
        "daily_trips_sampling": {
            "name": "normal",
            "mean": 3.143905,
            "std": 1.880373,
        },
        "num_days": 7*20,
    },
    "validation": {
        "gravity": {
            "beta": 0.03,
        },
        "spssim": {
            "quantiles": 100,
        }
    }
}

if __name__ == "__main__":
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print("RUN ID", run_id)
    run_directory = "{}/{}".format(results_dir, run_id)
    os.makedirs(run_directory, exist_ok=True)
    with open("{}/parameters.json".format(run_directory), 'w') as f:
        json.dump(params, f, indent=2)

    geotweets = mscthesis.read_geotweets_raw(params['input']['geotweets']).set_index('userid')
    home_locations = pd.read_csv(params['input']['home_locations']).set_index('userid')
    home_locations = gpd.GeoDataFrame(
        home_locations,
        crs="EPSG:3006",
        geometry=gpd.points_from_xy(home_locations.x, home_locations.y),
    )

    # remove users with less than 5 tweets
    # this code should be somewhere else...
    tweetcount = geotweets.groupby('userid').size()
    geotweets = geotweets.drop(labels=tweetcount[tweetcount < 5].index)

    model_region_sampling = None
    if params['model']['region_sampling']['name'] == 'zipf':
        model_region_sampling = models.RegionZipfProb(
            s=params['model']['region_sampling']['s'],
        )
    model_jump_size_sampling = None
    if params['model']['jump_size_sampling']['name'] == 'trueProb':
        model_jump_size_sampling = models.JumpSizeTrueProb()
    model = models.PreferentialReturn(
        p=params['model']['p'],
        gamma=params['model']['gamma'],
        region_sampling=model_region_sampling,
    )

    sampler_daily_trips_sampling = None
    if params['sampler']['daily_trips_sampling']['name'] == 'normal':
        sampler_daily_trips_sampling = models.NormalDistribution(
            mean=params['sampler']['daily_trips_sampling']['mean'],
            std=params['sampler']['daily_trips_sampling']['std'],
        )
    sampler = models.Sampler(
        model,
        daily_trips_sampling=sampler_daily_trips_sampling
    )
    print("sampling...")
    visits = sampler.sample(
        geotweets,
        n_days=params['sampler']['num_days'],
    )
    print()

    sampers = validation.Sampers()
    print("preparing sampers...")
    sampers.prepare()
    print()
    print("converting visits...")
    visits = sampers.convert(visits)
    print()

    results = []
    for scale in validation.scales:
        print("validating on scale", scale, "...")
        sparse_odm = sampers.align(
            scale,
            visits,
            home_locations,
        )
        sparse_odm = sampers.distance_cut(scale, sparse_odm)
        gm = validation.GravityModel(
            beta=params['validation']['gravity']['beta'],
        )
        seed_odm = gm.seed(sampers.distances[scale])
        dense_odm = gm.gravitate(sparse_odm, seed_odm)
        dense_odm = sampers.distance_cut(scale, dense_odm)

        odmfig = plots.plot_odms(sparse_odm, dense_odm, sampers.odm[scale])
        odmfig.savefig(
            "{}/odms-{}.png".format(run_directory, scale),
            bbox_inches='tight',
            dpi=140,
        )
        print("scoring on scale", scale, "...")
        spssim = validation.SPSSIM()
        score = spssim.score(
            sampers.odm[scale],
            dense_odm,
            sampers.quantile_groups[scale],
        )
        sampers_weighted_score = (score.score * score.sampers_weight).sum()
        print("sampers weighted score =", sampers_weighted_score)
        twitter_weighted_score = (score.score * score.twitter_weight).sum()
        print("twitter weighted score =", twitter_weighted_score)

        score.to_csv("{}/score-{}.csv".format(run_directory, scale))
        scorefig = plots.plot_spssim_score(score)
        scorefig.savefig("{}/score-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

        results.append({
            "scale": scale,
            "sampers_weighted_score": sampers_weighted_score,
            "twitter_weighted_score": twitter_weighted_score,
        })
        print()

    with open("{}/results.json".format(run_directory), 'w') as f:
        json.dump(results, f, indent=2)
