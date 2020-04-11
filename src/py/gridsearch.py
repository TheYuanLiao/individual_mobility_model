import json
import datetime
import os

import matplotlib.pyplot as plt

import models
import validation
import plots
import pipeline

results_dir = "./../../results"

if __name__ == "__main__":
    cfgs = pipeline.config_product(
        visit_factories=[
            models.Sampler(
                model=models.PreferentialReturn(
                    p=0.2,
                    gamma=0.8,
                    region_sampling=models.RegionTransitionZipf(beta=0.05, zipfs=1.2),
                    jump_size_sampling=models.JumpSizeTrueProb(),
                ),
                n_days=7 * 30,
                daily_trips_sampling=models.NormalDistribution(mean=3.14, std=1.8),
                geotweets_path="./../../dbs/sweden/geotweets.csv",
            ),  # Model
            # models.VisitsFromFile("./../../dbs/sweden/visits-zipf1.5.csv"),
        ],
        home_locations_paths=[
            "./../../dbs/sweden/homelocations.csv",
        ],
        gravity_models=[
            validation.GravityModel(beta=0.03),
            # validation.GravityModel(beta=0.025),
            # validation.GravityModel(beta=0.035),
        ]
    )
    pipe = pipeline.Pipeline()
    pipe.prepare()

    for cfg in cfgs:
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        print()
        print()
        print("RUNID", run_id)

        run_directory = "{}/{}".format(results_dir, run_id)
        os.makedirs(run_directory, exist_ok=True)
        with open("{}/parameters.json".format(run_directory), 'w') as f:
            json.dump(cfg.describe(), f, indent=2)

        result = pipe.run(cfg)
        pipe.visits.to_csv("./../../dbs/sweden/visits_{}.csv".format(run_id))
        spssim_scores = dict()
        for scale in validation.scales:
            odmfig = plots.plot_odms(
                [
                    result.sparse_odms[scale],
                    result.seed_odms[scale],
                    result.dense_odms[scale],
                    pipe.sampers.odm[scale]
                ],
                ['model', 'gravity_seed', 'gravity', 'sampers'],
            )
            odmfig.savefig("{}/odms-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

            score = result.spssim_scores[scale]
            score.to_csv("{}/score-{}.csv".format(run_directory, scale))

            spssimfig = plots.plot_spssim_score(score)
            spssimfig.savefig("{}/score-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

            sampers_weighted_score = (score.score * score.sampers_weight).sum()
            print("sampers weighted score =", sampers_weighted_score)
            twitter_weighted_score = (score.score * score.twitter_weight).sum()
            print("twitter weighted score =", twitter_weighted_score)
            spssim_scores[scale] = {
                "sampers_weighted_score": sampers_weighted_score,
                "twitter_weighted_score": twitter_weighted_score,
            }

            distance_metrics = result.distance_metrics[scale]
            distance_metrics.to_csv("{}/distance-metrics-{}.csv".format(run_directory, scale))

            dmfig = plots.plot_distance_metrics(distance_metrics, ['model', 'gravity_seed', 'gravity', 'sampers'])
            dmfig.savefig("{}/distance-metrics-{}.png".format(run_directory, scale), bbox_inches='tight', dpi=140)

        with open("{}/results.json".format(run_directory), 'w') as f:
            json.dump(spssim_scores, f, indent=2)

        # matplotlib keeps state (figures in global state)
        # We don't need the figures after writing to file so close them.
        # Otherwise memory usage will be immense.
        plt.close('all')
