import geopandas
from shapely.geometry import Polygon
import os
import subprocess


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

# dont want to break others using countries and assuming epsg:3035
countries_wgs = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
europe_wgs = countries_wgs[countries_wgs['continent'] == 'Europe'].dissolve(by='continent')

countries = countries_wgs.to_crs("EPSG:4326") # 3035
sweden = countries[countries['name'] == "Sweden"]
netherlands = countries[countries['name'] == "Netherlands"]

counties = geopandas.read_file(ROOT_dir + "/dbs/sweden/alla_lan/alla_lan.shp").to_crs("EPSG:3035")
gothenburg = counties[counties['ID'] == "14"]
stockholm = counties[(counties['ID'] == "01") | (counties['ID'] == '04') | (counties['ID'] == '03')]

sthlmcity = geopandas.GeoSeries([
    Polygon([(4750000, 4025000), (4750000, 4080000), (4800000, 4080000), (4800000, 4025000)])
],  crs=stockholm.crs)

gbgcity = geopandas.GeoSeries([
    Polygon([(4425000, 3830000), (4425000, 3865000), (4460000, 3865000), (4460000, 3830000)])
],  crs=gothenburg.crs)

sthlmoldtown = geopandas.GeoSeries([
    Polygon([
        (18.054753, 59.328335), (18.080074, 59.332052),
        (18.082627, 59.319851), (18.053841, 59.321979)
    ])
],  crs="EPSG:4326")
