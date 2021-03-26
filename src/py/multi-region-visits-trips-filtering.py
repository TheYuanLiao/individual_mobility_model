import os
import sys
import subprocess
import pandas as pd
import multiprocessing as mp
import geopandas as gpd
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

with open(ROOT_dir + '/lib/regions.yaml', encoding='utf8') as f:
    region_manager = yaml.load(f, Loader=yaml.FullLoader)


def filtering(region=None, runid=None):
    # The boundary to use when removing users based on location.
    metric_epsg = region_manager[region]['country_metric_epsg']
    zone_id = region_manager[region]['country_zone_id']
    zones_path = region_manager[region]['country_zones_path']
    zones = gpd.read_file(ROOT_dir + zones_path)
    zones = zones.loc[zones[zone_id].notnull()]
    zones = zones.rename(columns={zone_id: "zone"})
    zones.zone = zones.zone.astype(int)
    zones = zones.loc[zones.geometry.notnull()].to_crs(metric_epsg)
    if region != 'mexico':
        boundary = zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")
    else:
        boundary = zones.to_crs("EPSG:4326")
    print(boundary)
    print(region, 'boundary proccessed.')

    df = pd.read_csv(ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_trips.csv')
    # Origin
    print(region, 'filtering origins...')
    gdf = gpd.GeoDataFrame(
        df,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(df.longitude, df.latitude)
    )
    gdf = gpd.clip(gdf, boundary.convex_hull)
    gdf.drop(columns=['geometry'], inplace=True)

    # Destination
    print(region, 'filtering destinations...')
    gdf = gpd.GeoDataFrame(
        gdf,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(gdf.longitude_d, gdf.latitude_d)
    )
    gdf = gpd.clip(gdf, boundary.convex_hull)
    gdf.drop(columns=['geometry'], inplace=True)
    print(gdf.head())
    print(region, 'saving data...')
    gdf.to_csv(ROOT_dir + f'/dbs/{region}/visits/visits_{runid}_trips_dom.csv', index=False)


if __name__ == '__main__':
    region_list = ['sweden', 'netherlands', 'saopaulo', 'australia', 'austria', 'barcelona',
                   'capetown', 'cebu', 'egypt', 'guadalajara', 'jakarta',
                   'johannesburg', 'kualalumpur', 'lagos', 'madrid', 'manila', 'moscow', 'nairobi',
                   'rio', 'saudiarabia', 'stpertersburg', 'surabaya'] #,'mexicocity',
    runid = 6
    # parallelize the processing of geotagged tweets of multiple regions
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(filtering, [(r, runid, ) for r in region_list])
    pool.close()
    # filtering(region='nairobi', runid=runid)
