import os
import sys
import subprocess
import json
import time
import pandas as pd
import multiprocessing as mp


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')

import lib.mscthesis as mscthesis
import lib.models as models


class MultiRegionParaGenerate:
    def __init__(self, region=None):
        if not region:
            raise Exception("A valid region must be specified!")
        self.region = region
        self.path2visits = ROOT_dir + f'/dbs/{region}/visits/'
        if not os.path.exists(self.path2visits):
            os.makedirs(self.path2visits)
        self.path2geotweets = ROOT_dir + f'/dbs/{region}/geotweets.csv'
        if not os.path.exists(self.path2geotweets):
            raise Exception("The geotweets of the input region do not exist.")
        self.geotweets = None
        self.visits = None

    def load_geotweets(self, only_weekday=True):
        geotweets = mscthesis.read_geotweets_raw(self.path2geotweets).set_index('userid')
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
        self.geotweets = geotweets.sort_values(by=['userid', 'createdat'])

    def visits_gen_chunk(self, p=None, gamma=None, beta=None, days=None):
        visit_factory = models.Sampler(
            model=models.PreferentialReturn(
                p=p,
                gamma=gamma,
                region_sampling=models.RegionTransitionZipf(beta=beta, zipfs=1.2)
            ),
            n_days=days,
            daily_trips_sampling=models.NormalDistribution(mean=3.14, std=1.8)
        )
        # Calculate visits
        visits = visit_factory.sample(self.geotweets)
        return visits

    def visits_gen(self, p=None, gamma=None, beta=None, runid=None):
        # parallelize the generation of visits over days
        pool = mp.Pool(mp.cpu_count())
        tweets = self.geotweets
        visits_list = pool.starmap(self.visits_gen_chunk,
                                   [(p, gamma, beta, x) for x in [7] * 20])
        visits_total = pd.concat(visits_list).set_index('userid')
        pool.close()
        self.visits = visits_total
        if not os.path.exists(self.path2visits + f'visits_{runid}.csv'):
            self.visits.to_csv(self.path2visits + f'visits_{runid}.csv')
        with open(self.path2visits + 'paras.txt', 'a') as outfile:
            json.dump({'runid': runid, 'p': p, 'gamma': gamma, 'beta': beta}, outfile)
            outfile.write('\n')


if __name__ == '__main__':
    region_list = ['netherlands', 'sweden', 'saopaulo']
    p, gamma, beta = 0.8, 0.03, 0.3
    runid = 1
    for region2compute in region_list:
        # Start timing the code
        start_time = time.time()
        # prepare region data by initiating the class
        g = MultiRegionParaGenerate(region=region2compute)
        g.load_geotweets()
        g.visits_gen(p=p, gamma=gamma, beta=beta, runid=runid)
        print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))