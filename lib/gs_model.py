import os
import subprocess
import pandas as pd
import geopandas as gpd
import lib.models as models
import lib.validation as validation
import lib.mscthesis as mscthesis
import lib.genericvalidation as genericvalidation
import lib.sweden as sweden
import lib.saopaulo as saopaulo
import lib.netherlands as netherlands


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

region_path = {
    'sweden-national': {
        'home_locations_path': ROOT_dir + "/dbs/sweden/homelocations.csv",
        'tweets_calibration': ROOT_dir + "/dbs/sweden/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/sweden/geotweets_v.csv",
        'gt': sweden.GroundTruthLoader(scale='national')
    },
    'sweden-west': {
        'home_locations_path': ROOT_dir + "/dbs/sweden/homelocations.csv",
        'tweets_calibration': ROOT_dir + "/dbs/sweden/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/sweden/geotweets_v.csv",
        'gt': sweden.GroundTruthLoader(scale='west')
    },
    'sweden-east': {
        'home_locations_path': ROOT_dir + "/dbs/sweden/homelocations.csv",
        'tweets_calibration': ROOT_dir + "/dbs/sweden/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/sweden/geotweets_v.csv",
        'gt': sweden.GroundTruthLoader(scale='east')
    },
    'netherlands': {
        'home_locations_path': None,
        'tweets_calibration': ROOT_dir + "/dbs/netherlands/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/netherlands/geotweets_v.csv",
        'gt': netherlands.GroundTruthLoader()
    },
    'saopaulo': {
        'home_locations_path': None,
        'tweets_calibration': ROOT_dir + "/dbs/saopaulo/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/saopaulo/geotweets_v.csv",
        'gt': saopaulo.GroundTruthLoader()
    }
}


class RegionDataPrep:
    """
    RegionDataPrep will preload Twitter data for calibration, validation, home locations
    and ground truth (zones & data)
    """
    def __init__(self, region=None):
        if region is None:
            raise Exception("A region must be set")
        self.region = region
        self.bbox = None
        self.zones = None
        self.gt_odm = None
        self.distances = None
        self.distance_quantiles = None
        self.home_locations = None
        self.tweets_calibration = None
        self.tweets_validation = None
        self.kl_baseline = None
        self.dms = None

    def load_zones_odm(self):
        ground_truth = region_path[self.region]['gt']
        self.bbox = ground_truth.bbox

        # load zones
        ground_truth.load_zones()
        # load odm
        ground_truth.load_odm()

        # assign values of zones and gt_odm
        self.zones = ground_truth.zones
        self.gt_odm = ground_truth.odm

        # print("Calculating distances...")
        self.distances = genericvalidation.zone_distances(self.zones)
        # print("Calculating distance quantiles...")
        self.distance_quantiles = genericvalidation.distance_quantiles(self.distances)
        if self.region == 'sweden-national':
            self.gt_odm[self.distances < 100] = 0
            self.gt_odm = self.gt_odm / self.gt_odm.sum()
        self.dms = validation.DistanceMetrics().compute(
            self.distance_quantiles,
            [self.gt_odm],
            ['groundtruth']
        )

    def load_geotweets(self, type='calibration', only_weekday=True):
        if type == 'calibration':
            geotweets_path = region_path[self.region]['tweets_calibration']
        else:
            geotweets_path = region_path[self.region]['tweets_validation']
        geotweets = mscthesis.read_geotweets_raw(geotweets_path).set_index('userid')
        if only_weekday:
            # Only look at weekday trips
            geotweets = geotweets[(geotweets['weekday'] < 6) & (0 < geotweets['weekday'])]
        # Remove users who don't have home visit in geotweets
        home_visits = geotweets.query("label == 'home'").groupby('userid').size()
        geotweets = geotweets.loc[home_visits.index]
        # read home locations
        if 'sweden' in self.region:
            home_locations = pd.read_csv(region_path[self.region]['home_locations_path']).set_index('userid')
            self.home_locations = gpd.GeoDataFrame(
                home_locations,
                crs="EPSG:4326",
                geometry=gpd.points_from_xy(home_locations.longitude, home_locations.latitude),
            ).to_crs("EPSG:3006")
        # Remove users with less than 20 tweets
        tweetcount = geotweets.groupby('userid').size()
        geotweets = geotweets.drop(labels=tweetcount[tweetcount < 20].index)
        # Remove users with only one region
        regioncount = geotweets.groupby(['userid', 'region']).size().groupby('userid').size()
        geotweets = geotweets.drop(labels=regioncount[regioncount < 2].index)
        # Ensure the tweets are sorted chronologically
        if type == 'calibration':
            self.tweets_calibration = geotweets.sort_values(by=['userid', 'createdat'])
        else:
            self.tweets_validation = geotweets.sort_values(by=['userid', 'createdat'])

    def kl_baseline_compute(self):
        self.dms = validation.DistanceMetrics().compute(
            self.distance_quantiles,
            [self.gt_odm],
            ['groundtruth']
        )
        self.dms.loc[:, 'baseline_sum'] = 0
        self.dms.loc[self.dms['groundtruth_sum'] != 0, 'baseline_sum'] = 1 / len(self.dms.loc[self.dms['groundtruth_sum'] != 0, :])
        self.kl_baseline = validation.DistanceMetrics().kullback_leibler(self.dms, titles=['groundtruth', 'baseline'])


class VisitsGeneration:
    """
    VisitsGeneration take region and its zones, odm, and distance groups as initiated.
    It generate visits and compare the odm_model with the ground truth.
    It returns the kl divergence measure quantifying the similarity between the above two distance distributions.
    """
    def __init__(self, region=None, bbox=None, zones=None, odm=None,
                 distances=None, distance_quantiles=None, gt_dms=None):
        self.region = region
        self.zones = zones
        self.odm = odm
        self.distances = distances
        self.distance_quantiles = distance_quantiles
        self.gt_dms = gt_dms
        self.bbox = bbox

    def visits_gen_chunk(self, geotweets=None, p=None, gamma=None, beta=None, days=None):
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
        visits = visit_factory.sample(geotweets)
        return visits

    def visits2measure(self, visits=None, home_locations=None):
        if 'sweden' in self.region:
            n_visits_before = visits.shape[0]
            home_locations_in_sampling = gpd.sjoin(home_locations, self.bbox)
            visits = visits[visits.index.isin(home_locations_in_sampling.index)]
            print("removed", n_visits_before - visits.shape[0], "visits due to sampling bbox")
        model_odm = genericvalidation.visits_to_odm(visits, self.zones)
        if self.region == 'sweden-national':
            model_odm[self.distances < 100] = 0
        dms = validation.DistanceMetrics().compute(
            self.distance_quantiles,
            [model_odm],
            ['model']
        )
        dms.loc[:, 'groundtruth_sum'] = self.gt_dms['groundtruth_sum']
        divergence_measure = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])
        return dms, divergence_measure
