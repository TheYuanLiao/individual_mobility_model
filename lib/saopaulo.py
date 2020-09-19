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
        self.metric_epsg = "EPSG:22523"


class GroundTruthLoader:
    def __init__(self):
        self.zones = None
        self.odm = None
        self.boundary = None
        self.zones_pop = None
        self.bbox = None

    def load_zones(self):
        _zones = gpd.read_file(ROOT_dir + '/dbs/saopaulo/zones/zones.shp')
        self.zones = _zones.rename(columns={"NumeroZona": "zone"})[['zone', 'geometry']]

    def zone_populations(self):
        sheet = pd.read_excel(ROOT_dir + "/dbs/saopaulo/population.xlsx", skiprows=6, index_col=0, skipfooter=17, sheet_name=0)
        census = sheet.dropna().reset_index('Zona ').rename(
            columns={'População': 'census_population', 'Zona ': 'zone'})
        census['zone'] = census['zone'].astype('int64')
        census = census.set_index('zone').census_population
        self.zones_pop = self.zones.set_index('zone').join(census)

    def boundary(self):
        self.boundary = self.zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")

    def load_odm(self):
        odms = pd.read_excel(ROOT_dir + "/dbs/saopaulo/odm/odm.xlsx", skiprows=7, index_col=0, skipfooter=3).drop(columns="Total")
        assert odms.shape[0] == 517
        assert odms.shape[1] == 517
        odms = odms.stack()
        self.odm = odms / odms.sum()

