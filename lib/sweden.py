import geopandas as gpd
import os
import lib.sampers as sampers
import pandas as pd
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
        self.counties = gpd.read_file(ROOT_dir + '/dbs/alla_lan/alla_lan.shp')
        self.boundary = self.counties.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")


class GroundTruthLoader:
    def __init__(self, scale=None):
        self.scale = scale
        self.zones = None
        self.odm = None
        self.bbox = sampers.bbox[self.scale]

    def load_zones(self):
        self.zones = sampers.read_shp(sampers.shps[self.scale])

    def load_odm(self):
        odm = sampers.read_odm(sampers.odms[self.scale]).set_index(['ozone', 'dzone'])['total']
        print("odm", odm.shape, odm.sum())
        # ODM file can contain trips between zones that are not actually part of the scale.
        # Drop trips between unknown zones and
        # insert 0.0 trips between zones that are not represented in ODM
        print("Reindexing...")
        zones_x = self.zones.set_index('zone')
        odm = odm.reindex(
            pd.MultiIndex.from_product([
                zones_x.index,
                zones_x.index,
            ]),
            fill_value=0.0,
        )
        print("odm", odm.shape)
        self.odm = odm / odm.sum()
