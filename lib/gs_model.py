import os
import subprocess
import pandas as pd
import geopandas as gpd
import lib.models as models
import lib.validation as validation
import lib.helpers as helpers
import lib.genericvalidation as genericvalidation
import lib.sweden_sv as sweden_sv
import lib.saopaulo as saopaulo
import lib.netherlands as netherlands


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))  # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

region_path = {
    'sweden': {
        'home_locations_path': ROOT_dir + "/dbs/sweden/homelocations.csv",
        'tweets_calibration': ROOT_dir + "/dbs/sweden/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/sweden/geotweets_v.csv",
        'gt': sweden_sv.GroundTruthLoader()
    },
    'netherlands': {
        'home_locations_path': ROOT_dir + "/dbs/netherlands/homelocations.csv",
        'tweets_calibration': ROOT_dir + "/dbs/netherlands/geotweets_c.csv",
        'tweets_validation': ROOT_dir + "/dbs/netherlands/geotweets_v.csv",
        'gt': netherlands.GroundTruthLoader()
    },
    'saopaulo': {
        'home_locations_path': ROOT_dir + "/dbs/saopaulo/homelocations.csv",
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
        self.trip_distances = None
        self.distance_quantiles = None
        self.home_locations = None
        self.tweets_calibration = None
        self.tweets_validation = None
        self.bm_odm = None  # benchmark odm
        self.kl_baseline = None  # benchmark vs groundtruth
        self.kl_deviation = None  # groundtruth vs groundtruth_true
        self.dms = None
        self.dms_true = None
        self.dms_bm = None

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
        if self.region == 'sweden-national':
            self.gt_odm[self.distances < 100] = 0
            self.gt_odm = self.gt_odm / self.gt_odm.sum()

        # calculate ODM-based distances
        self.distances = genericvalidation.zone_distances(self.zones)

        # calculate distance quantiles and get the bins for potential processing of the actual trip distances
        self.distance_quantiles, bins = genericvalidation.distance_quantiles(self.distances)

        # fetch the raw trip distances if ground_truth.trip_distances is not None
        if ground_truth.trip_distances is not None:
            self.trip_distances = ground_truth.trip_distances
            self.trip_distances.loc[:, 'distance'] = pd.cut(self.trip_distances.distance, bins, right=True)
            self.dms_true = pd.DataFrame(self.trip_distances.groupby('distance')['weight'].sum())
            self.dms_true.loc[:, 'weight'] = self.dms_true.loc[:, 'weight'] / sum(self.dms_true.loc[:, 'weight'])
            self.dms_true = self.dms_true.rename(columns={'weight': 'groundtruth_true_sum'})

        # Calculate zone-based distance distribution
        self.dms = validation.DistanceMetrics().compute(
            self.distance_quantiles,
            [self.gt_odm],
            ['groundtruth']
        )

    def load_geotweets(self, type='calibration', only_weekday=True):
        # 1. Load geotweets
        if type == 'calibration':
            geotweets_path = region_path[self.region]['tweets_calibration']
        else:
            geotweets_path = region_path[self.region]['tweets_validation']
        geotweets = helpers.read_geotweets_raw(geotweets_path).set_index('userid')
        if only_weekday:
            # Only look at weekday trips
            geotweets = geotweets[(geotweets['weekday'] < 6) & (0 < geotweets['weekday'])]
        # Remove users who don't have home visit in geotweets
        home_visits = geotweets.query("label == 'home'").groupby('userid').size()
        geotweets = geotweets.loc[home_visits.index]
        # read home locations
        self.home_locations = pd.read_csv(region_path[self.region]['home_locations_path']).set_index('userid')
        if 'sweden' in self.region:
            self.home_locations = gpd.GeoDataFrame(
                self.home_locations,
                crs="EPSG:4326",
                geometry=gpd.points_from_xy(self.home_locations.longitude, self.home_locations.latitude),
            ).to_crs("EPSG:3006")
        # Remove users with less than 20 tweets
        tweetcount = geotweets.groupby('userid').size()
        geotweets = geotweets.drop(labels=tweetcount[tweetcount < 20].index)
        # Remove users with only one region
        regioncount = geotweets.groupby(['userid', 'region']).size().groupby('userid').size()
        geotweets = geotweets.drop(labels=regioncount[regioncount < 2].index)
        # Ensure the tweets are sorted chronologically and the geometry is dropped
        if type == 'calibration':
            self.tweets_calibration = geotweets.sort_values(by=['userid', 'createdat']).drop(columns=['geometry'])
            tweets = self.tweets_calibration.copy()
        else:
            self.tweets_validation = geotweets.sort_values(by=['userid', 'createdat']).drop(columns=['geometry'])
            tweets = self.tweets_validation.copy()

        # 2. Create benchmark odm from geotweets directly
        tweets.loc[:, 'kind'] = 'region'
        self.bm_odm = genericvalidation.visits_to_odm(tweets, self.zones, timethreshold_hours=24)
        if self.region == 'sweden-national':
            self.bm_odm[self.distances < 100] = 0
        # Save bm_odm in dbs for visualization purpose
        if type == 'calibration':
            benchmark_path = ROOT_dir + '/dbs/' + self.region + '/odm_benchmark_c.csv'
        else:
            benchmark_path = ROOT_dir + '/dbs/' + self.region + '/odm_benchmark_v.csv'
        if ~os.path.exists(benchmark_path):
            bm_odm2save = self.bm_odm.copy()
            bm_odm2save = bm_odm2save.reset_index()
            bm_odm2save.columns = ['ozone', 'dzone', 'benchmark']
            print('Saving bm_odm... \n', bm_odm2save.head())
            bm_odm2save.to_csv(benchmark_path)

        # Calculate zone-based distance distribution for benchmark
        self.dms_bm = validation.DistanceMetrics().compute(
            self.distance_quantiles,
            [self.bm_odm],
            ['benchmark']
        )

    def kl_baseline_compute(self):
        # groundtruth, benchmark
        self.dms.loc[:, 'benchmark_sum'] = self.dms_bm.loc[:, 'benchmark_sum'].values
        if self.dms_true is not None:
            # groundtruth, benchmark, groundtruth_true
            self.dms.loc[:, 'groundtruth_true_sum'] = self.dms_true.loc[:, 'groundtruth_true_sum'].values
            self.kl_deviation = validation.DistanceMetrics().kullback_leibler(self.dms, titles=['groundtruth', 'groundtruth_true'])
        self.kl_baseline = validation.DistanceMetrics().kullback_leibler(self.dms, titles=['groundtruth', 'benchmark'])


class VisitsGeneration:
    """
    VisitsGeneration takes region and its zones, odm, and distance groups as initiated.
    It generates visits and compare the odm_model with the ground truth.
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

    def visits_gen(self, geotweets=None, p=None, gamma=None, beta=None, days=None, homelocations=None):
        visit_factory = models.Sampler(
            model=models.PreferentialReturn(
                p=p,
                gamma=gamma,
                region_sampling=models.RegionTransitionZipf(beta=beta, zipfs=1.2)
            ),
            n_days=days,
            daily_trips_sampling=models.WeightedDistribution()
        )
        # Calculate visits
        visits = visit_factory.sample(geotweets)

        # Add weight if applicable
        if 'weight' in homelocations:
            visits = pd.merge(visits, homelocations.loc[:, ['weight']],
                              left_index=True, right_index=True)
        return visits

    def visits2measure(self, visits=None, home_locations=None):
        if 'sweden-' in self.region:
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
        for var in ['groundtruth_sum', 'groundtruth_true_sum', 'benchmark_sum']:
            if var in self.gt_dms.columns:
                dms.loc[:, var] = self.gt_dms.loc[:, var].values
        divergence_measure = validation.DistanceMetrics().kullback_leibler(dms, titles=['groundtruth', 'model'])
        return dms, divergence_measure, model_odm
