import sys
import subprocess
import os
import multiprocessing as mp
import pandas as pd


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')

import lib.gs_model as gs_model
import time
import json


class RegionParaGenerate:
    def __init__(self, res=None, region=None, rg=None, visits=None):
        self.res = res
        self.region = region
        self.rg = rg
        self.visits = visits

    def region_data_load(self, type='calibration'):
        if '-' not in self.region:
            self.res = ROOT_dir + '/dbs/' + self.region + '/visits/' + type + '.csv'
        else:
            self.res = ROOT_dir + '/dbs/sweden/visits/' + self.region.split('-')[1] + '_' + type + '.csv'
        rg_ = gs_model.RegionDataPrep(region=self.region)
        rg_.load_zones_odm()
        rg_.load_geotweets(type=type)
        rg_.kl_baseline_compute()
        self.rg = rg_
        # Save gt_odm in dbs for visualization purpose
        gt_path = ROOT_dir + '/dbs/' + self.region + '/odm_gt.csv'
        if ~os.path.exists(gt_path):
            gt_odm2save = self.rg.gt_odm.copy()
            gt_odm2save = gt_odm2save.reset_index()
            gt_odm2save.columns = ['ozone', 'dzone', 'gt']
            print('Saving gt_odm... \n', gt_odm2save.head())
            gt_odm2save.to_csv(gt_path)
        self.visits = gs_model.VisitsGeneration(region=self.region, bbox=self.rg.bbox,
                                                zones=self.rg.zones, odm=self.rg.gt_odm,
                                                distances=self.rg.distances,
                                                distance_quantiles=self.rg.distance_quantiles, gt_dms=self.rg.dms)

    def visits_gen(self, type='calibration', p=None, gamma=None, beta=None):
        if type == 'calibration':
            tweets = self.rg.tweets_calibration
        else:
            tweets = self.rg.tweets_validation
        # userid as index for visits_total
        visits_total = self.visits.visits_gen(tweets, p, gamma, beta,
                                              days=260, homelocations=self.rg.home_locations)
        dms, _, model_odm = self.visits.visits2measure(visits=visits_total, home_locations=self.rg.home_locations)
        # Save model_odm in dbs for visualization purpose
        model_odm = model_odm.reset_index()
        model_odm.columns = ['ozone', 'dzone', 'model']
        print('Saving model_odm... \n', model_odm.head())
        model_odm.to_csv(ROOT_dir + '/dbs/' + self.region + '/odm_' + type + '.csv')
        dms.to_csv(ROOT_dir + '/results/grid-search/' + self.region + '_' + type + '_distances.csv')


if __name__ == '__main__':
    file = ROOT_dir + '/results/grid-search/gridsearch.txt'
    list_lines = []
    with open(file) as f:
        for jsonObj in f:
            line = json.loads(jsonObj)
            list_lines.append(line)
    df = pd.DataFrame(list_lines)
    # ['sweden-west', 'sweden-east', 'netherlands', 'saopaulo', 'sweden-national']
    for region2compute in ['sweden', 'netherlands']: #, 'netherlands', 'saopaulo'
        # Start timing the code
        start_time = time.time()
        dc = df.loc[df['region'] == region2compute, ['p', 'beta', 'gamma']].to_dict('records')[0]
        # prepare region data by initiating the class
        gs = RegionParaGenerate(region=region2compute)
        for tp in ('calibration', 'validation'):
            gs.region_data_load(type=tp)
            gs.visits_gen(type=tp, p=dc['p'], gamma=dc['gamma'], beta=dc['beta'])
        print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))
