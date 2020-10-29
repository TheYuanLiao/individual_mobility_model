"""
Extract the zones and origin-destination matrix for visualization purpose
Author: Yuan Liao
Purpose: To develope a data product that explores the origin-destination matrix using the travel survey.
Region: The Netherlands
"""
import os
import sys
import subprocess
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

import lib.netherlands as netherlands


def load_odm(gt, hour=None):
    """
    :param gt: a class that loads zones and odm
    """
    odm_list = []
    for m_id, m_name in zip([0, 1, 2, 4], ['Non-bike', 'E-bike', 'Bike', 'Total']):
        gt.load_odm_visualization(mode=m_id, hour=hour)
        ser = gt.odm
        ser.name = m_name
        odm_list.append(ser)
        print(f"Hour {hour} / mode {m_name} is done.")
    # Combine mode-specific odms
    df = pd.concat(odm_list, axis=1)

    # Remove zero cells
    df = df.loc[(df != 0).any(axis=1)]

    # Rename MultiIndex and reset
    df.index.names = ['ozone', 'dzone']
    df = df.reset_index()
    df.loc[:, 'hour'] = hour # total
    print(f"Hour {hour} is done.")
    return df


if __name__ == '__main__':
    time_list_1 = list(range(0, 13))
    time_list_2 = list(range(12, 25))
    # Prepare the class for loading data
    ground_truth = netherlands.GroundTruthLoader()
    # load zones
    ground_truth.load_zones()

    # parallelize the processing of geotagged tweets of multiple regions
    pool = mp.Pool(mp.cpu_count())
    df_list_1 = pool.starmap(load_odm, [(ground_truth, hr, ) for hr in time_list_1])
    pool.close()

    # parallelize the processing of geotagged tweets of multiple regions
    pool = mp.Pool(mp.cpu_count())
    df_list_2 = pool.starmap(load_odm, [(ground_truth, hr, ) for hr in time_list_2])
    pool.close()

    # Save ODMs and zones
    df_list = df_list_1 + df_list_2
    df = pd.concat(df_list)
    df.to_csv(ROOT_dir + '/dbs/netherlands/odms_vis/odms_by_mode.csv', index=False)
    ground_truth.zones.to_file(ROOT_dir + '/dbs/netherlands/odms_vis/zones.shp')