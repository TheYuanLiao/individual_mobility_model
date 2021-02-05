import os
import sys
import subprocess
import json
import time
import pandas as pd
import geopandas as gpd
import multiprocessing as mp
import yaml


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')

with open(ROOT_dir + '/lib/regions.yaml') as f:
    region_manager = yaml.load(f, Loader=yaml.FullLoader)

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
        # Load region data
        self.region_info = region_manager[self.region]
        self.zones = None
        self.boundary = None

    def country_zones_boundary_load(self):
        # The boundary to use when removing users based on location.
        zones_loader = self.region_info['zones_loader']
        metric_epsg = self.region_info['country_metric_epsg']
        zone_id = self.region_info['country_zone_id']
        zones_path = self.region_info['country_zones_path']

        if zones_loader == 1:
            zones = gpd.read_file(ROOT_dir + zones_path)
            zones = zones.loc[zones[zone_id].notnull()]
            zones = zones.rename(columns={zone_id: "zone"})
            zones.zone = zones.zone.astype(int)
            self.zones = zones.loc[zones.geometry.notnull()].to_crs(metric_epsg)
            self.boundary = self.zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")

    def load_geotweets(self, only_weekday=True, only_domestic=True):
        geotweets = mscthesis.read_geotweets_raw(self.path2geotweets)
        if only_weekday:
            # Only look at weekday trips
            geotweets = geotweets[(geotweets['weekday'] < 6) & (0 < geotweets['weekday'])]
        # Check if keeps only domestic geotagged tweets
        if only_domestic:
            geotweets = gpd.GeoDataFrame(
                geotweets,
                crs="EPSG:4326",
                geometry=gpd.points_from_xy(geotweets.longitude, geotweets.latitude)
            )
            geotweets = gpd.clip(geotweets, self.boundary.convex_hull)
            geotweets.drop(columns=['geometry'], inplace=True)
        geotweets = geotweets.set_index('userid')
        # Remove users who don't have home visit in geotweets
        home_visits = geotweets.query("label == 'home'").groupby('userid').size()
        geotweets = geotweets.loc[home_visits.index]
        # Remove users with less than 20 tweets
        tweetcount = geotweets.groupby('userid').size()
        geotweets = geotweets.drop(labels=tweetcount[tweetcount < 20].index) # This is for domestic trip generation
        # Remove users with only one region
        regioncount = geotweets.groupby(['userid', 'region']).size().groupby('userid').size()
        geotweets = geotweets.drop(labels=regioncount[regioncount < 2].index)
        # Ensure the tweets are sorted chronologically
        self.geotweets = geotweets.sort_values(by=['userid', 'createdat'])

    def visits_gen(self, p=None, gamma=None, beta=None, days=None, runid=None):
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
        self.visits = visit_factory.sample(self.geotweets)
        print("Visits generation is done. Now saving...")
        # # parallelize the generation of visits over days
        # visits_total_gpd = gpd.GeoDataFrame(
        #     visits_total,
        #     crs='EPSG:4326',
        #     geometry=gpd.points_from_xy(visits_total['longitude'], visits_total['latitude'])
        # )
        # visits_total_inland = gpd.clip(visits_total_gpd, self.boundary.convex_hull)
        # visits_total.loc[visits_total.index.isin(visits_total_inland.index), 'dom'] = 1
        # visits_total.loc[~visits_total.index.isin(visits_total_inland.index), 'dom'] = 0
        if not os.path.exists(self.path2visits + f'visits_{runid}.csv'):
            self.visits.to_csv(self.path2visits + f'visits_{runid}.csv')
        with open(self.path2visits + 'paras.txt', 'a') as outfile:
            json.dump({'runid': runid, 'p': p, 'gamma': gamma, 'beta': beta}, outfile)
            outfile.write('\n')


if __name__ == '__main__':
    runid = 5
    days = 260

    # # The regions lacking ground truth data
    # region_list = ['austria', 'barcelona', 'capetown', 'australia',
    #                'cebu', 'egypt', 'guadalajara', 'jakarta', 'johannesburg', 'kualalumpur',
    #                'lagos', 'madrid', 'manila', 'mexicocity', 'moscow', 'nairobi',
    #                'rio', 'saudiarabia', 'stpertersburg', 'surabaya']
    # p, gamma, beta = 0.93, 0.18, 0.21
    # for region2compute in region_list:
    #     # Start timing the code
    #     start_time = time.time()
    #     # prepare region data by initiating the class
    #     print(f'{region2compute} started...')
    #     g = MultiRegionParaGenerate(region=region2compute)
    #     print('Loading zones to get boundary...')
    #     g.country_zones_boundary_load()
    #     print('Loading geotagged tweets...')
    #     g.load_geotweets(only_domestic=True)
    #     print('Generating visits...')
    #     g.visits_gen(p=p, gamma=gamma, beta=beta, days=days, runid=runid)
    #     print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))

    # The regions with ground truth data
    region_dict = {'sweden': (0.92, 0.07, 0.05),
                   'netherlands': (0.98, 0.35, 0.04),
                   'saopaulo': (0.89, 0.11, 0.53)}
    for region2compute, para in region_dict.items():
        if region2compute == 'netherlands':
            p, gamma, beta = para[0], para[1], para[2]
            # Start timing the code
            start_time = time.time()
            # prepare region data by initiating the class
            print(f'{region2compute} started...')
            g = MultiRegionParaGenerate(region=region2compute)
            print('Loading zones to get boundary...')
            g.country_zones_boundary_load()
            print('Loading geotagged tweets...')
            g.load_geotweets(only_domestic=True)
            print('Generating visits...')
            g.visits_gen(p=p, gamma=gamma, beta=beta, days=days, runid=runid)
            print(region2compute, "is done. Elapsed time was %g seconds" % (time.time() - start_time))
