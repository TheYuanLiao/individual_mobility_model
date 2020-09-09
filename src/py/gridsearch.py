import json
import datetime
import os

import matplotlib.pyplot as plt

import models
import validation
import plots
import pipeline

results_dir = os.getcwd() + "/results"

ps = [0.2, 0.4] #[0.3, 0.6, 0.9]
gammas = [0.7, 0.9] #[0.2, 0.5, 0.8]
betas = [0.02, 0.04]

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
                    geotweets_path=os.getcwd() + "/dbs/sweden/geotweets_c.csv",
                )
            )

for f in visit_factories:
    print(f.describe())


if __name__ == "__main__":
    cfgs = pipeline.config_product(
        visit_factories=visit_factories,
        home_locations_paths=[
            os.getcwd() + "/dbs/sweden/homelocations.csv",
        ]
    )
    pipe = pipeline.Pipeline()
    pipe.prepare()

    for cfg in cfgs:
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        print()
        print()
        print("RUNID", run_id)

        run_directory = "{}/{}-{}".format(results_dir, 'sweden', run_id)
        os.makedirs(run_directory, exist_ok=True)
        with open("{}/parameters.json".format(run_directory), 'w') as f:
            json.dump(cfg.describe(), f, indent=2)

        result = pipe.run(cfg)
        pipe.visits.to_csv(os.getcwd() + "/dbs/sweden/visits/{}.csv".format(run_id))
        for scale in validation.scales:
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
