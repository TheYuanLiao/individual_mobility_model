import sys
import subprocess
import os


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))  # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')


import lib.gs_model as gs_model
import pprint
import time
from bayes_opt import BayesianOptimization
from bayes_opt.util import UtilityFunction, Colours
import asyncio
import threading

try:
    import json
    import tornado.ioloop
    import tornado.httpserver
    from tornado.web import RequestHandler
    import requests
except ImportError:
    raise ImportError(
        "In order to run this example you must have the libraries: " +
        "`tornado` and `requests` installed."
    )

# Start timing the code
start_time = time.time()

res = ROOT_dir + '/results/gridsearch-n.txt'

# prepare region data
region = 'sweden-west'
rg = gs_model.RegionDataPrep(region=region)
rg.load_zones_odm()
rg.load_geotweets()
rg.kl_baseline_compute()
print('Region', region, ': baseline kl measure =', rg.kl_baseline)
visits = gs_model.VisitsGeneration(region=region, bbox=rg.bbox,
                                   zones=rg.zones, odm=rg.gt_odm,
                                   distances=rg.distances,
                                   distance_quantiles=rg.distance_quantiles, gt_dms=rg.dms)


def gs_para(p, beta, gamma):
    # Read Points of Destination - The file points.csv contains the columns GEOID, X and Y [inside]
    divergence_measure = visits.visits_gen(geotweets=rg.tweets_calibration, home_locations=rg.home_locations,
                                           p=p, gamma=gamma, beta=beta)
    # append the result to the gridsearch file
    dic = {'region': region, 'p': p, 'beta': beta, 'gamma': gamma,
           'kl-baseline': rg.kl_baseline, 'kl': divergence_measure}
    pprint.pprint(dic)
    with open(res, 'a') as outfile:
        json.dump(dic, outfile)
        outfile.write('\n')
    return -divergence_measure


class BayesianOptimizationHandler(RequestHandler):
    """Basic functionality for NLP handlers."""
    _bo = BayesianOptimization(
        f=gs_para,
        pbounds={'p': (0, 1), 'beta': (0, 1), 'gamma': (0, 1)}
    )
    _uf = UtilityFunction(kind="ucb", kappa=3, xi=1)

    def post(self):
        """Deal with incoming requests."""
        body = tornado.escape.json_decode(self.request.body)

        try:
            self._bo.register(
                params=body["params"],
                target=body["target"],
            )
            print("BO has registered: {} points.".format(len(self._bo.space)), end="\n\n")
        except KeyError:
            pass
        finally:
            suggested_params = self._bo.suggest(self._uf)

        self.write(json.dumps(suggested_params))


def run_optimization_app():
    asyncio.set_event_loop(asyncio.new_event_loop())
    handlers = [
        (r"/bayesian_optimization", BayesianOptimizationHandler),
    ]
    server = tornado.httpserver.HTTPServer(
        tornado.web.Application(handlers)
    )
    server.listen(9009)
    tornado.ioloop.IOLoop.instance().start()


def run_optimizer():
    global optimizers_config
    config = optimizers_config.pop()
    name = config["name"]
    colour = config["colour"]

    register_data = {}
    max_target = None
    for _ in range(10):
        status = name + " wants to register: {}.\n".format(register_data)

        resp = requests.post(
            url="http://localhost:9009/bayesian_optimization",
            json=register_data,
        ).json()
        target = gs_para(**resp)

        register_data = {
            "params": resp,
            "target": target,
        }

        if max_target is None or target > max_target:
            max_target = target

        status += name + " got {} as target.\n".format(target)
        status += name + " will to register next: {}.\n".format(register_data)
        print(colour(status), end="\n")

    global results
    results.append((name, max_target))
    print(colour(name + " is done!"), end="\n\n")


if __name__ == "__main__":
    ioloop = tornado.ioloop.IOLoop.instance()
    optimizers_config = [
        {"name": "optimizer 1", "colour": Colours.red},
        {"name": "optimizer 2", "colour": Colours.green},
        {"name": "optimizer 3", "colour": Colours.blue},
    ]

    app_thread = threading.Thread(target=run_optimization_app)
    app_thread.daemon = True
    app_thread.start()

    targets = (
        run_optimizer,
        run_optimizer,
        run_optimizer
    )
    optimizer_threads = []
    for target in targets:
        optimizer_threads.append(threading.Thread(target=target))
        optimizer_threads[-1].daemon = True
        optimizer_threads[-1].start()

    results = []
    for optimizer_thread in optimizer_threads:
        optimizer_thread.join()

    for result in results:
        print(result[0], "found a maximum value of: {}".format(result[1]))

    ioloop.stop()
    print("Elapsed time was %g seconds" % (time.time() - start_time))
