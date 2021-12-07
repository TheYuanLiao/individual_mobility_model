import sys
import subprocess
import os
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
import lib.validation as validation


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
        self.visits = gs_model.VisitsGeneration(region=self.region, bbox=self.rg.bbox,
                                                zones=self.rg.zones, odm=self.rg.gt_odm,
                                                distances=self.rg.distances,
                                                distance_quantiles=self.rg.distance_quantiles, gt_dms=self.rg.dms)

    def visits_gen_by_days(self, type='calibration', p=None, gamma=None, beta=None, days=None):
        if type == 'calibration':
            tweets = self.rg.tweets_calibration
        else:
            tweets = self.rg.tweets_validation
        # userid as index for visits_total
        visits_total = self.visits.visits_gen(tweets, p, gamma, beta,
                                              days=days, homelocations=self.rg.home_locations)
        dms, _, _ = self.visits.visits2measure(visits=visits_total, home_locations=self.rg.home_locations)
        kl = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])
        print("D=", days, " kl=", kl)
        return kl


if __name__ == '__main__':
    file = ROOT_dir + '/results/para-search-r1/parasearch.txt'
    list_lines = []
    with open(file) as f:
        for jsonObj in f:
            line = json.loads(jsonObj)
            list_lines.append(line)
    df = pd.DataFrame(list_lines)
    list_df_res = []
    for region2compute in ['sweden', 'netherlands', 'saopaulo']:
        # Start timing the code
        start_time = time.time()
        dc = df.loc[df['region'] == region2compute, ['p', 'beta', 'gamma']].to_dict('records')[0]
        # Prepare region data by initiating the class
        gs = RegionParaGenerate(region=region2compute)
        tp = 'calibration'
        gs.region_data_load(type=tp)
        list_kl = [gs.visits_gen_by_days(type=tp, p=dc['p'], gamma=dc['gamma'], beta=dc['beta'], days=day) for day in
                   [1, 5] + [x*10 for x in range(1, 31)]]
        df_res = pd.DataFrame()
        df_res.loc[:, 'days'] = [1, 5] + [x*10 for x in range(1, 31)]
        df_res.loc[:, 'kl'] = list_kl
        df_res.loc[:, 'region'] = region2compute
        list_df_res.append(df_res)
        print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))
    df_res = pd.concat(list_df_res)
    df_res.to_csv(ROOT_dir + "/results/parameter_D_KL_relationship.csv", index=False)
