import sys
import subprocess
import os
import pandas as pd
import numpy as np


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
import lib.helpers as hp


def downsample(data, N_max):
    temp = data.head(N_max)
    if 'home' in temp.label.values:
        return temp


class RegionParaGenerate:
    def __init__(self, res=None, region=None, rg=None, visits=None):
        self.res = res
        self.region = region
        self.rg = rg
        self.visits = visits
        self.odm_gt = None

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
        # Assign odm_gt for later comparison
        if self.odm_gt is None:
            self.odm_gt = self.rg.gt_odm.copy()
            self.odm_gt = self.odm_gt.reset_index()
            self.odm_gt.columns = ['ozone', 'dzone', 'gt']
        self.visits = gs_model.VisitsGeneration(region=self.region, bbox=self.rg.bbox,
                                                zones=self.rg.zones, odm=self.rg.gt_odm,
                                                distances=self.rg.distances,
                                                distance_quantiles=self.rg.distance_quantiles, gt_dms=self.rg.dms)

    def visits_gen_by_nmax(self, type='calibration', p=None, gamma=None, beta=None, N_max=None):
        if type == 'calibration':
            tweets = self.rg.tweets_calibration
        else:
            tweets = self.rg.tweets_validation
        # Downsample all Twitter users' data to N_max if needed
        if N_max is not None:
            tweets = tweets.reset_index().groupby('userid').apply(lambda data: downsample(data, N_max)).\
                reset_index(drop=True).set_index('userid')
            # Remove users with only one region
            regioncount = tweets.groupby(['userid', 'region']).size().groupby('userid').size()
            tweets = tweets.drop(labels=regioncount[regioncount < 2].index)
        n_total = len(tweets)
        # userid as index for visits_total
        visits_total = self.visits.visits_gen(tweets, p, gamma, beta,
                                              days=260, homelocations=self.rg.home_locations)
        dms, _, model_odm = self.visits.visits2measure(visits=visits_total, home_locations=self.rg.home_locations)
        kl = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])
        # SSI
        model_odm = model_odm.reset_index()
        model_odm.columns = ['ozone', 'dzone', 'model']
        df = pd.merge(self.odm_gt, model_odm, on=['ozone', 'dzone'])
        ssi = hp.ssi_dataframe(df, var1='gt', var2='model')
        print("N_max=", N_max, " kl=", kl, " ssi=", ssi)
        return n_total, kl, ssi

    def visits_gen_by_indi(self, type='calibration', p=None, gamma=None, beta=None, indi_list=None):
        if type == 'calibration':
            tweets = self.rg.tweets_calibration
        else:
            tweets = self.rg.tweets_validation
        # Downsample all Twitter users' data to N_max if needed
        if indi_list is not None:
            tweets = tweets.loc[tweets.index.isin(indi_list), :]
            # Remove users with only one region
            regioncount = tweets.groupby(['userid', 'region']).size().groupby('userid').size()
            tweets = tweets.drop(labels=regioncount[regioncount < 2].index)
        n_total = len(tweets)
        # userid as index for visits_total
        visits_total = self.visits.visits_gen(tweets, p, gamma, beta,
                                              days=260, homelocations=self.rg.home_locations)
        dms, _, model_odm = self.visits.visits2measure(visits=visits_total, home_locations=self.rg.home_locations)
        kl = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])
        # SSI
        model_odm = model_odm.reset_index()
        model_odm.columns = ['ozone', 'dzone', 'model']
        df = pd.merge(self.odm_gt, model_odm, on=['ozone', 'dzone'])
        ssi = hp.ssi_dataframe(df, var1='gt', var2='model')
        print("# of users=", len(indi_list), " kl=", kl, " ssi=", ssi)
        return len(indi_list), n_total, kl, ssi


if __name__ == '__main__':
    file = ROOT_dir + '/results/para-search-r1/parasearch.txt'
    list_lines = []
    with open(file) as f:
        for jsonObj in f:
            line = json.loads(jsonObj)
            list_lines.append(line)
    df = pd.DataFrame(list_lines)
#    list_df_res = []
    list_df_res_indi = []
    for region2compute in ['sweden', 'netherlands', 'saopaulo']:
        # Start timing the code
        start_time = time.time()
        dc = df.loc[df['region'] == region2compute, ['p', 'beta', 'gamma']].to_dict('records')[0]
        # Prepare region data by initiating the class
        gs = RegionParaGenerate(region=region2compute)
        tp = 'calibration'
        gs.region_data_load(type=tp)

        # Model performance as a function of number of users (randomly drawn)
        if tp == 'calibration':
            tw = gs.rg.tweets_calibration
        else:
            tw = gs.rg.tweets_valibration
        # df_user = tw.groupby('userid').size().to_frame('size').reset_index().sort_values(by='size').reset_index(drop=True)
        df_user = tw.groupby('userid').size().to_frame('size').reset_index().sample(frac=1).reset_index(drop=True)
        group_size = np.floor(len(df_user) / 10)
        indi_list_list = [df_user.loc[:x, 'userid'].values for x in [group_size*i for i in [1, 2, 3, 4, 5, 6, 7, 8, 9]] + [len(df_user)]]
        list_res_indi = [gs.visits_gen_by_indi(type=tp, p=dc['p'], gamma=dc['gamma'],
                                                  beta=dc['beta'], indi_list=indi_list)
                            for indi_list in indi_list_list]
        df_res_indi = pd.DataFrame(list_res_indi, columns=['n_indi', 'n_total', 'kl', 'ssi'])
        df_res_indi.loc[:, 'region'] = region2compute
        list_df_res_indi.append(df_res_indi)

        # # Model performance as a function of maximum number of geolocations each users
        # nmax_list = [30, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 100000]
        # list_res = [gs.visits_gen_by_nmax(type=tp, p=dc['p'], gamma=dc['gamma'], beta=dc['beta'], N_max=N_max)
        #            for N_max in nmax_list]
        # df_res = pd.DataFrame(list_res, columns=['n_total', 'kl', 'ssi'])
        # df_res.loc[:, 'nmax'] = nmax_list
        # df_res.loc[:, 'region'] = region2compute
        # list_df_res.append(df_res)


        print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))
    # df_res = pd.concat(list_df_res)
    # df_res.to_csv(ROOT_dir + "/results/N_KL_relationship.csv", index=False)
    df_res_indi = pd.concat(list_df_res_indi)
    df_res_indi.to_csv(ROOT_dir + "/results/Nindi_KL_relationship.csv", index=False)