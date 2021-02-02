import sys
import subprocess
import os


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')

import json
import lib.gs_model as gs_model
import pprint
import time
from bayes_opt import BayesianOptimization
from bayes_opt.logger import JSONLogger
from bayes_opt.event import Events


class RegionParaSearch:
    def __init__(self, res=None, region=None, rg=None, visits=None):
        self.res = res
        self.region = region
        self.rg = rg
        self.visits = visits

    def region_data_load(self):
        self.res = ROOT_dir + '/results/grid-search/gridsearch-n_' + self.region + '.txt'
        rg_ = gs_model.RegionDataPrep(region=self.region)
        rg_.load_zones_odm()
        rg_.load_geotweets()
        rg_.kl_baseline_compute()
        self.rg = rg_
        self.visits = gs_model.VisitsGeneration(region=self.region, bbox=self.rg.bbox,
                                                zones=self.rg.zones, odm=self.rg.gt_odm,
                                                distances=self.rg.distances,
                                                distance_quantiles=self.rg.distance_quantiles, gt_dms=self.rg.dms)

    def gs_para(self, p=None, gamma=None, beta=None):
        # userid as index for visits_total
        visits_total = self.visits.visits_gen(self.rg.tweets_calibration, p, gamma, beta, days=140)

        # # parallelize the generation of visits over days
        # pool = mp.Pool(mp.cpu_count())
        # visits_list = pool.starmap(self.visits.visits_gen_chunk,
        #                            [(self.rg.tweets_calibration, p, gamma, beta, x) for x in [7] * 20])
        # visits_total = pd.concat(visits_list).set_index('userid')
        # pool.close()

        print('Visits generated:', len(visits_total))
        _, divergence_measure, _ = self.visits.visits2measure(visits=visits_total, home_locations=self.rg.home_locations)
        # append the result to the gridsearch file
        dic = {'region': self.region, 'p': p, 'beta': beta, 'gamma': gamma,
               'kl-baseline': self.rg.kl_baseline, 'kl': divergence_measure}
        pprint.pprint(dic)
        with open(self.res, 'a') as outfile:
            json.dump(dic, outfile)
            outfile.write('\n')
        return -divergence_measure


if __name__ == '__main__':
    # ['sweden-west', 'sweden-east', 'netherlands', 'saopaulo', 'sweden-national']
    for region2search in ['sweden', 'netherlands', 'saopaulo']:
        # prepare region data by initiating the class
        gs = RegionParaSearch(region=region2search)
        gs.region_data_load()

        # Start timing the code
        start_time = time.time()

        # Bounded region of parameter space
        pbounds = {'p': (0.01, 0.99), 'gamma': (0.01, 0.99), 'beta': (0.01, 0.99)}

        optimizer = BayesianOptimization(
            f=gs.gs_para,
            pbounds=pbounds,
            random_state=98,
        )

        logger = JSONLogger(path=ROOT_dir + "/results/grid-search/logs_" + gs.region + ".json")
        optimizer.subscribe(Events.OPTIMIZATION_STEP, logger)
        optimizer.maximize(
            init_points=8,
            n_iter=50,
        )
        print(optimizer.max)
        print(region2search, "is done. Elapsed time was %g seconds" % (time.time() - start_time))
