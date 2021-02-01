import geopandas as gpd
import pandas as pd
import os
import subprocess


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()


class GeoInfo:
    def __init__(self):
        self.metric_epsg = "EPSG:3035"
        self.counties = gpd.read_file(ROOT_dir + '/dbs/sweden/alla_lan/alla_lan.shp')
        self.boundary = self.counties.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")


class GroundTruthLoader:
    def __init__(self):
        self.zones = None
        self.odm = None
        self.boundary = None
        self.bbox = None

    def load_zones(self):
        _zones = gpd.read_file(ROOT_dir + '/dbs/sweden/survey_deso/DeSO/DeSO_2018_v2.shp')
        self.zones = _zones.rename(columns={"deso": "zone"})[['zone', 'geometry']]

    def boundary(self):
        self.boundary = self.zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")

    def load_odm(self):
        trips = pd.read_csv(ROOT_dir + "/dbs/sweden/survey_deso/day_trips.csv")
        trips = trips.loc[:, ["sub_id", 'date', "origin_main_deso", "desti_main_deso", 'trip_weight']]
        trips["T"] = trips["date"].apply(lambda x: pd.to_datetime(x))
        trips = trips.loc[~trips["T"].apply(lambda x: x.weekday()).isin([5, 6]), :]
        trips.dropna(axis=0, how='any', inplace=True)
        odms = trips.groupby(['origin_main_deso', 'desti_main_deso']).sum()['trip_weight']
        print(odms.head())
        z = self.zones.zone
        odms = odms.reindex(pd.MultiIndex.from_product([z, z]), fill_value=0)
        print(odms.head())
        self.odm = odms / odms.sum()
