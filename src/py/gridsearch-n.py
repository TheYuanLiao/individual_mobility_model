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

import json
import lib.gs_model as gs_model
import pprint
import time
import multiprocessing as mp
import gc

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

# make a list of jobs to do
jobs = []
for p in [0.1, 0.2]:
    for beta in [0.03]:
        for gamma in [0.8]:
            jobs.append((p, beta, gamma))


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
    gc.collect()
    return dic


# Step 1: Init multiprocessing.Pool()
pool = mp.Pool(mp.cpu_count() - 1)

# Step 2: `pool.apply` the `gs_para()`
pool.starmap(gs_para, jobs)

# Step 3: Don't forget to close
pool.close()
print("Elapsed time was %g seconds" % (time.time() - start_time))
