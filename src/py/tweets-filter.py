import os
import subprocess
import yaml
import time
import pandas as pd
import geopandas as gpd
import lib.mscthesis as mscthesis


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

with open(ROOT_dir + '/lib/regions.yaml') as f:
    region_manager = yaml.load(f, Loader=yaml.FullLoader)


def get_homelocations(ts):
    _ts = ts.query('label == "home"').groupby(['userid', 'region']).head(1)
    return gpd.GeoDataFrame(
        _ts,
        crs='EPSG:4326',
        geometry=gpd.points_from_xy(_ts['longitude'], _ts['latitude'])
    )


class TweetsFilter:
    def __init__(self, region=None):
        # Define the focus region
        self.region = region
        self.boundary = None
        self.zones = None
        # Load region data
        self.region_info = region_manager[self.region]

        # Which sqlite3 file to get geotweets from
        if os.path.exists(ROOT_dir + f"/dbs/{region}/{region}.sqlite3"):
            self.sqlite_geotweets = ROOT_dir + f"/dbs/{region}/{region}.sqlite3"
        else:
            raise Exception(f"The folder and .sqlite3 file do not exist for region, {self.region}")

        # Where to save CSVs for geotweets and homelocations
        self.csv_geotweets = ROOT_dir + f"/dbs/{region}/geotweets.csv"
        self.csv_homelocations = ROOT_dir + f"/dbs/{region}/homelocations.csv"

        # Place holder for the processed geotagged tweets
        self.geotweets = None
        self.homelocations = None

    def zones_boundary_load(self):
        # The boundary to use when removing users based on location.
        zones_loader = self.region_info['zones_loader']
        metric_epsg = self.region_info['metric_epsg']
        zone_id = self.region_info['zone_id']
        zones_path = self.region_info['zones_path']

        if zones_loader == 1:
            zones = gpd.read_file(ROOT_dir + zones_path)
            zones = zones[zones[zone_id].notnull()]
            zones = zones.rename(columns={zone_id: "zone"})
            zones.zone = zones.zone.astype(int)
            self.zones = zones[zones.geometry.notnull()].to_crs(metric_epsg)
            self.boundary = self.zones.assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")

    def tweets_filter_1(self):
        # Load geotweets from .sqlite
        geotweets = mscthesis.tweets_from_sqlite(self.sqlite_geotweets)

        # 1 Filter out geotweets without precise geolocation information or more than 50
        coord_counts = geotweets.groupby(['latitude', 'longitude']).size().sort_values(ascending=False)
        coord_percentages = (coord_counts / geotweets.shape[0]).to_frame("perc").reset_index()
        percentages_to_remove = coord_percentages[coord_percentages.perc > 0.001]
        perc_filter = None
        for (_, row) in percentages_to_remove.iterrows():
            f = (geotweets.latitude != row.latitude) & (geotweets.longitude != row.longitude)
            if perc_filter is None:
                perc_filter = f
            else:
                perc_filter = perc_filter & f

        print("Removing ", perc_filter[~perc_filter].size, "center-of-region geotweets")
        geotweets = geotweets[perc_filter]
        geotweets['createdat'] = pd.to_datetime(geotweets['createdat'], infer_datetime_format=True)
        geotweets = geotweets.set_index(['userid', 'createdat']).sort_index()
        tweet_count_before = geotweets.groupby('userid').size()
        self.geotweets = geotweets.drop(
            labels=tweet_count_before[tweet_count_before <= 50].index,
            level=0,
        )

    def tweets_filter_2(self):
        # 2 Remove home...
        geotweets = self.geotweets.reset_index('createdat')
        geotweets = geotweets.assign(ym=geotweets['createdat'].dt.to_period('M'))

        # Get home locations
        geotweetsx = mscthesis.cluster(geotweets)
        geotweetsx = mscthesis.label_home(geotweetsx)

        # Only keep the latest home location and the relevant records
        geotweetsx = mscthesis.remove_tweets_outside_home_period(geotweetsx)
        homelocations = get_homelocations(geotweetsx)
        self.homelocations = gpd.clip(homelocations, self.boundary.convex_hull)

        # Only keep those users who live in the study area
        geotweetsy = geotweetsx[geotweetsx.index.isin(self.homelocations.index)]
        self.geotweets = geotweetsy

    def tweets_save(self):
        if not os.path.exists(self.csv_geotweets):
            self.geotweets.to_csv(self.csv_geotweets)
        if not os.path.exists(self.csv_homelocations):
            self.homelocations[['latitude', 'longitude']].to_csv(self.csv_homelocations)


if __name__ == '__main__':
    region = 'austria'
    # Loading zones
    start_time = time.time()
    tl = TweetsFilter(region=region)
    tl.zones_boundary_load()
    print(f"{region}: zone loading is done with the elapsed time was %g seconds" % (time.time() - start_time))

    # Filtering geotweets - 1
    start_time = time.time()
    tl.tweets_filter_1()
    print(f"{region}: geotweets filtering 1 is done with the elapsed time was %g seconds" % (time.time() - start_time))

    # Filtering geotweets - 2
    start_time = time.time()
    tl.tweets_filter_2()
    print(f"{region}: geotweets filtering 2 is done with the elapsed time was %g seconds" % (time.time() - start_time))
    tl.tweets_save()