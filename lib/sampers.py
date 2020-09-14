import geopandas
import pandas
import regions
import os
import subprocess


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

shps = {
    "national": ROOT_dir + "/dbs/sampers/national/region.shp",
    "west": ROOT_dir + "/dbs/sampers/west/region.shp",
    "east": ROOT_dir + "/dbs/sampers/east/region.shp",
}

odms = {
    "national": ROOT_dir + "/dbs/sampers/national/trips.csv",
    "west":  ROOT_dir + "/dbs/sampers/west/trips.csv",
    "east": ROOT_dir + "/dbs/sampers/east/trips.csv",
}

bbox = {
    "national": regions.counties.to_crs("EPSG:3006"),
    "east": regions.counties[regions.counties['ID'].isin(['01', '03', '04', '09', '18', '19'])].to_crs('EPSG:3006'),
    "west": regions.counties[regions.counties['ID'].isin(['13', '14', '17'])].to_crs('EPSG:3006')
}


def read_shp(path):
    return geopandas.read_file(path).rename(columns={'te_csv_Bor': 'zone', 'K_vast': 'zone', 'K_samm': 'zone'})


def read_odm(path):
    return pandas.read_csv(path)

