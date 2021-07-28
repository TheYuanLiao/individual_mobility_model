import os
import sys
import subprocess
import geopandas as gpd
import time
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

import lib.helpers as helpers


class MultiRegionDriveNetworkDownloader:
    def __init__(self, region=None):
        if not region:
            raise Exception("A valid region must be specified!")
        self.region = region
        self.boundary = None
        self.osm_path = ROOT_dir + f'/dbs/{region}/osm/'

    def boundary_loader(self):
        # The boundary to use when downloading drive networks
        metric_epsg = region_manager[self.region]['metric_epsg']
        zone_id = region_manager[self.region]['zone_id']
        zones_path = region_manager[self.region]['zones_path']
        zones = gpd.read_file(ROOT_dir + zones_path)
        zones = zones.loc[zones[zone_id].notnull()]
        zones = zones.rename(columns={zone_id: "zone"})
        zones.zone = zones.zone.astype(int)
        zones = zones.loc[zones.geometry.notnull()].to_crs(metric_epsg)
        if self.region != 'mexico':
            self.boundary = zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")
        else:
            self.boundary = zones.to_crs("EPSG:4326")
        print(self.region, 'boundary proccessed.')

    def network_downloader(self):
        helpers.osm_downloader(boundary=self.boundary, osm_path=self.osm_path, regenerating_shp=True)


def downloader(region=None):
    # Start timing the code
    start_time = time.time()
    dl = MultiRegionDriveNetworkDownloader(region=region)
    dl.boundary_loader()
    dl.network_downloader()
    print(region, "is done. Elapsed time was %g seconds" % (time.time() - start_time))


if __name__ == '__main__':
    region_list = ['surabaya', 'stpertersburg', 'barcelona', 'capetown', 'cebu', 'guadalajara',
                   'johannesburg', 'kualalumpur', 'madrid', 'nairobi']

    for region in region_list:
        print(region)
        try:
            downloader(region=region)
        except:
            print(region, 'failed.')
            pass
