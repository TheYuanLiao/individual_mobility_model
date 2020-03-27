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

if __name__ == "__main__":
    input_geotweets = "./../../dbs/sweden/geotweets.csv"
    input_home_locations = "./../../dbs/sweden/homelocations.csv"

    geotweets = mscthesis.read_geotweets_raw(input_geotweets).set_index('userid')
    home_locations = pd.read_csv(input_home_locations).set_index('userid')
    home_locations = gpd.GeoDataFrame(
        home_locations,
        crs="EPSG:3006",
        geometry=gpd.points_from_xy(home_locations.x, home_locations.y),
    )

    # remove users with less than 5 tweets
    # this code should be somewhere else...
    tweetcount = geotweets.groupby('userid').size()
    geotweets = geotweets.drop(labels=tweetcount[tweetcount < 5].index)

    sampers = validation.Sampers()
    print("preparing sampers...")
    sampers.prepare()

    for s in [1.0, 1.2, 1.5]:
        model = models.PreferentialReturn(
            p=0.66,
            gamma=0.6,
            region_sampling=models.RegionZipfProb(s=s),
            jump_size_sampling=models.JumpSizeTrueProb(),
        )
        sampler = models.Sampler(
            model=model,
            daily_trips_sampling=models.NormalDistribution(mean=3.143905, std=1.880373),
            n_days=7 * 20,
        )
        visits = sampler.sample(geotweets)
        visits.to_csv('./../../dbs/sweden/visits-zipf{}.csv'.format(s))

        visits = sampers.convert(visits)
        for beta in [0.025, 0.03, 0.035]:
            gm = validation.GravityModel(beta=beta)

            # Output
            params = {
                "input": {
                    "geotweets": input_geotweets,
                    "home_locations": input_home_locations,
                },
                "sampler": sampler.describe(),
                "gravity": gm.describe(),
            }
            run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            print()
            print()
            print("RUN ID", run_id)
            run_directory = "{}/{}".format(results_dir, run_id)
            os.makedirs(run_directory, exist_ok=True)
            with open("{}/parameters.json".format(run_directory), 'w') as f:
                json.dump(params, f, indent=2)
            results = []
            for scale in validation.scales:
                sparse_odm = sampers.align(scale=scale, home_locations=home_locations, visits=visits)
                sparse_odm = sampers.distance_cut(scale=scale, odm=sparse_odm)
                seed_odm = gm.seed(sampers.distances[scale])
                dense_odm = gm.gravitate(sparse_odm=sparse_odm, seed=seed_odm)
                dense_odm = sampers.distance_cut(scale=scale, odm=dense_odm)

                odmfig = plots.plot_odms(sparse_odm, dense_odm, sampers.odm[scale])
                odmfig.savefig(
                    "{}/odms-{}.png".format(run_directory, scale),
                    bbox_inches='tight',
                    dpi=140,
                )

                score = mscthesis.spssim(sampers.odm[scale], dense_odm, sampers.distances[scale], nquantiles=100)

                sampers_weighted_score = (score.score * score.sampers_weight).sum()
                print("sampers weighted score =", sampers_weighted_score)
                twitter_weighted_score = (score.score * score.twitter_weight).sum()
                print("twitter weighted score =", twitter_weighted_score)

                scorefig = plots.plot_spssim_score(score)
                scorefig.savefig(
                    "{}/score-{}.png".format(run_directory, scale),
                    bbox_inches='tight',
                    dpi=140,
                )
                score.to_csv("{}/score-{}.csv".format(run_directory, scale))
                results.append({
                    "scale": scale,
                    "sampers_weighted_score": sampers_weighted_score,
                    "twitter_weighted_score": twitter_weighted_score,
                })
            with open("{}/results.json".format(run_directory), 'w') as f:
                json.dump(results, f, indent=2)