import os
import sys
import subprocess
import numpy as np
import pandas as pd
import multiprocessing as mp
from tqdm import tqdm


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


class MultiRegionVisitsDesc:
    def __init__(self, region=None, runid=None):
        if not region:
            raise Exception("A valid region must be specified!")
        if not runid:
            raise Exception("A valid runid must be specified!")
        self.region = region
        self.runid = runid
        self.path2visits = ROOT_dir + f'/dbs/{region}/visits/visits_{runid}.csv'
        if not os.path.exists(self.path2visits):
            raise Exception(f"The visits_{runid}.csv of the input region does not exist.")
        self.visits = None
        self.visits_stats = None
        self.path2visits_stats = ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_stats.csv'
        self.path2visits_trips = ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_trips.csv'

    def user_proc(self, data):
        data = data.copy()
        data.loc[data['timeslot'] == 0, 'day_n'] = range(1, len(data.loc[data['timeslot'] == 0, 'day']) + 1)
        data.loc[:, 'day_n'] = data.loc[:, 'day_n'].fillna(method='ffill').astype(int)
        return data

    def user_day_proc(self, data):
        data2 = data.copy()
        data2.loc[:, 'latitude_d'] = np.vstack((data2[1:].latitude.values.reshape(len(data2) - 1, 1),
                                                data2[:1].latitude.values.reshape(1, 1)))
        data2.loc[:, 'longitude_d'] = np.vstack((data2[1:].longitude.values.reshape(len(data2) - 1, 1),
                                                 data2[:1].longitude.values.reshape(1, 1)))
        #data2.loc[:, 'dom_d'] = np.vstack((data2[1:].dom.values.reshape(len(data2) - 1, 1),
        #                                   data2[:1].dom.values.reshape(1, 1)))
        data2.loc[:, 'distance'] = data2.apply(
            lambda row: mscthesis.haversine_distance(row['latitude'], row['longitude'],
                                                     row['latitude_d'], row['longitude_d']), axis=1)
        #data2.loc[:, 'inland'] = data2.apply(lambda row: 1 if (row['dom'] == 1) & (row['dom_d'] == 1) else 0, axis=1)
        return pd.Series({'pkt': data2['distance'].sum(),
                          'num_trip': len(data2),
                          'pkt_inland': data2.loc[:, 'distance'].sum(), #data2['inland'] == 1
                          'num_trip_inland': len(data2)}) #data2['inland'] == 1

    def user_day_proc_distance(self, data):
        data2 = data.copy()
        data2.loc[:, 'latitude_d'] = np.vstack((data2[1:].latitude.values.reshape(len(data2) - 1, 1),
                                                data2[:1].latitude.values.reshape(1, 1)))
        data2.loc[:, 'longitude_d'] = np.vstack((data2[1:].longitude.values.reshape(len(data2) - 1, 1),
                                                 data2[:1].longitude.values.reshape(1, 1)))
        #data2.loc[:, 'dom_d'] = np.vstack((data2[1:].dom.values.reshape(len(data2) - 1, 1),
        #                                   data2[:1].dom.values.reshape(1, 1)))
        data2.loc[:, 'distance'] = data2.apply(
            lambda row: mscthesis.haversine_distance(row['latitude'], row['longitude'],
                                                     row['latitude_d'], row['longitude_d']), axis=1)
        #data2.loc[:, 'inland'] = data2.apply(lambda row: 1 if (row['dom'] == 1) & (row['dom_d'] == 1) else 0, axis=1)
        return data2.loc[:, ['userid', 'timeslot', 'day_n', 'distance',
                             'latitude', 'longitude', 'latitude_d', 'longitude_d']]

    def load_visits_preprocess(self):
        df_v = pd.read_csv(self.path2visits)
        self.visits = df_v.groupby('userid').apply(self.user_proc).reset_index(drop=True)

    def visits_desc_compute(self, aggregation=True):
        tqdm.pandas(desc=self.region)
        if aggregation:
            self.visits_stats = self.visits.groupby(['userid', 'day_n']).progress_apply(self.user_day_proc).reset_index()
            self.visits_stats.to_csv(self.path2visits_stats, index=False)
        else:
            self.visits_stats = self.visits.groupby(['userid', 'day_n']).progress_apply(self.user_day_proc_distance).reset_index(drop=True)
            self.visits_stats.to_csv(self.path2visits_trips, index=False)


def region_visits_proc(region=None, runid=None, aggregation=True):
    rg = MultiRegionVisitsDesc(region=region, runid=runid)
    rg.load_visits_preprocess()
    rg.visits_desc_compute(aggregation=aggregation)


if __name__ == '__main__':
    region_list = ['saopaulo', 'australia', 'austria', 'barcelona', 'sweden', 'netherlands', 'capetown',
                   'cebu', 'egypt', 'guadalajara', 'jakarta', 'johannesburg', 'kualalumpur', 'nairobi',
                   'lagos', 'madrid', 'manila', 'mexicocity', 'moscow',
                   'rio', 'saudiarabia', 'stpertersburg', 'surabaya']
    runid = 6
    # If agg set to False, then the trips will be logged, otherwise, the aggregate statistics will be logged
    agg = False
    # parallelize the processing of geotagged tweets of multiple regions
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(region_visits_proc, [(r, runid, agg, ) for r in region_list])
    pool.close()
    # Single region test
    # region_visits_proc('nairobi', runid, aggregation=agg)
