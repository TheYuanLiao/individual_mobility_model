import pandas as pd
import geopandas as gpd
import numpy as np
import sqlite3
from sklearn.cluster import DBSCAN
import os
import osmnx as ox
import math


def osm_downloader(boundary=None, osm_path=None, regenerating_shp=False):
    """
    Download drive network within a certain geographical boundary.
    :param boundary:
    geodataframe of the area for downloading the network.

    :param osm_path:
    file path to save the network in .shp and .graphml.

    :param regenerating_shp:
    if needs to regenerating the shape file.

    :return:
    None
    """
    minx, miny, maxx, maxy = boundary.geometry.total_bounds
    new_network = osm_path + 'drive.graphml'
    new_network_shp = osm_path + 'drive.shp'

    def shp_processor(G, new_network_shp):
        print('Processing graphml to GeoDataframe...')
        gdf_n = ox.graph_to_gdfs(G)
        edge = gdf_n[1]
        edge = edge.loc[:, ['geometry', 'highway', 'junction', 'length', 'maxspeed', 'name', 'oneway',
                            'osmid', 'u', 'v', 'width', 'lanes']]
        fields = ['osmid', 'u', 'v', 'length', 'maxspeed', 'oneway']
        df_inter = pd.DataFrame()
        for f in fields:
            df_inter[f] = edge[f].astype(str)
        gdf_edge = gpd.GeoDataFrame(df_inter, geometry=edge["geometry"])
        gdf_edge = gdf_edge.rename(columns={'osmid': 'osm_id', 'maxspeed': 'max_speed'})

        print('Saving as shp...')
        gdf_edge.to_file(new_network_shp)

    if not os.path.exists(new_network):
        print('Downloading graphml...')
        G = ox.graph_from_bbox(maxy, miny, maxx, minx, network_type='drive')
        print('Saving as graphml...')
        ox.save_graphml(G, filepath=new_network)
        if not os.path.exists(new_network_shp):
            shp_processor(G, new_network_shp)
    else:
        if regenerating_shp:
            print('Loading graphml...')
            G = ox.load_graphml(new_network)
            shp_processor(G, new_network_shp)
        if not os.path.exists(new_network_shp):
            print('Loading graphml...')
            G = ox.load_graphml(new_network)
            shp_processor(G, new_network_shp)
        else:
            print('Drive networks exist. Skip downloading.')


def filter_trips(df=None, boundary=None):
    """
    Filter trips within a certain geographical boundary.
    :param boundary:
    geodataframe of the area for downloading the network.

    :param df, dataframe:
    [userid, timeslot, day_n, distance, latitude, longitude, latitude_d, longitude_d].

    :return:
    Filtered trips, dataframe
    [userid, timeslot, day_n, distance, latitude, longitude, latitude_d, longitude_d].
    """
    # Origin
    print('Filtering origins...')
    gdf = gpd.GeoDataFrame(
        df,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(df.longitude, df.latitude)
    )
    gdf = gpd.clip(gdf, boundary.convex_hull)
    gdf.drop(columns=['geometry'], inplace=True)

    # Destination
    print('Filtering destinations...')
    gdf = gpd.GeoDataFrame(
        gdf,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(gdf.longitude_d, gdf.latitude_d)
    )
    gdf = gpd.clip(gdf, boundary.convex_hull)
    gdf.drop(columns=['geometry'], inplace=True)
    return gdf


def cluster(ts, eps_km=0.1, min_samples=1):
    """
    Clusters each users tweets with DBSCAN.
    :param ts:
    [userid*, latitude, longitude, ...rest]

    :param eps_km:
    eps parameter of DBSCAN expressed in kilometers.

    :param min_samples:
    min_samples parameter of DBSCAN.

    :return:
    [userid*, latitude, longitude, region, ...rest]
    """

    def f(_ts):
        kms_per_radian = 6371.0088
        coords_rad = np.radians(_ts[['latitude', 'longitude']].values)
        cls = DBSCAN(eps=eps_km / kms_per_radian, min_samples=min_samples, metric='haversine').fit(coords_rad)
        return _ts.assign(region=pd.Series(cls.labels_, index=_ts.index).values)

    regions = ts.groupby('userid', as_index=False).apply(f)
    return regions


def during_home(ts):
    """
    Only returns tweets that are during "home-hours".
    """
    weekdays = (ts['weekday'] < 6) & (0 < ts['weekday'])
    weekends = (ts['weekday'] == 6) | (0 == ts['weekday'])
    morning_evening = (ts['hourofday'] < 9) | (17 < ts['hourofday'])
    return ts[((weekdays) & (morning_evening)) | (weekends)]


def label_home(ts):
    """
    Labels the most visited region during "home-hours" as home.

    input: (* = index)
    [userid*, region, ...rest]

    output:
    [userid*, region, label, ...rest]
    """
    _ts = ts.copy(deep=True)
    _ts = _ts.reset_index().set_index(['userid', 'region']).sort_index()
    _ts = _ts.assign(
        label=pd.Series(dtype=str, index=_ts.index).fillna('other'),
    )
    homeidxs = during_home(_ts) \
        .groupby(['userid', 'region']).size() \
        .groupby('userid').nlargest(1) \
        .droplevel(0).index
    _ts.loc[homeidxs, 'label'] = 'home'
    return _ts.reset_index().set_index('userid')


def gaps(df):
    dtypes = df.dtypes.to_dict()
    df_or = df.shift(1).dropna().astype(dtypes).reset_index(drop=True)
    df_ds = df.shift(-1).dropna().astype(dtypes).reset_index(drop=True)
    df = df_or.join(df_ds, lsuffix="_origin", rsuffix="_destination")
    df = df.assign(duration=df['createdat_destination'] - df['createdat_origin'])
    return df


def visit_gaps(visits):
    """
    :param visits:
     DataFrame of visits indexed by "userid".
     [userid*, ...rest]
    :return:
     DataFrame of gaps between visits for each user.
     [userid*, ...rest_origin, ...rest_destination]
    """

    def f(user_visits):
        origins = user_visits.shift(1).dropna().astype(visits.dtypes.to_dict()).reset_index(drop=True)
        destinations = user_visits.shift(-1).dropna().astype(visits.dtypes.to_dict()).reset_index(drop=True)
        return origins.join(destinations, lsuffix="_origin", rsuffix="_destination")

    return visits.groupby('userid').apply(f).reset_index(level=1, drop=True)


geotweet_paths = {
    "sweden": os.getcwd() + "/dbs/sweden/geotweets.csv",
    "sweden_infered": os.getcwd() + "/dbs/sweden/geotweets_infered.csv",
}


def read_geotweets_raw(path):
    ts = pd.read_csv(path)
    ts["createdat"] = pd.to_datetime(ts.createdat, infer_datetime_format=True)
    return gpd.GeoDataFrame(
        ts,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(ts.longitude, ts.latitude),
    )


def tweets_from_sqlite(db):
    conn = sqlite3.connect(db)
    df_raw = pd.read_sql_query("SELECT * FROM geo_tweet order by user_id", con=conn)
    return df_raw.rename(columns={
        'tweet_id': 'tweetid',
        'user_id': 'userid',
        'created_at': 'createdat',
        'hour_of_day': 'hourofday',
        'time_zone': 'timezone'
    })


def remove_tweets_outside_home_period(ts):
    """
    Remove tweets that are outside of detected home's time range.
    input: (* = index)
    [userid*, label, createdat, ...rest]

    output:
    [userid*, label, createdat, ...rest]
    """

    def f(_ts):
        homes = _ts[_ts['label'] == 'home']
        start = homes['createdat'].min()
        end = homes['createdat'].max()
        return _ts[(start <= _ts['createdat']) & (_ts['createdat'] <= end)]

    return ts.groupby('userid').apply(f).droplevel(0)


def coordinates_bearing(lats1, lngs1, lats2, lngs2):
    """
    Calculates the bearing (degrees, 0 is north, clock-wise) elementwise.
    :return:
    Bearing.
    """
    dLons = (lngs2 - lngs1)
    ys = np.sin(dLons) * np.cos(lats2)
    xs = np.cos(lats1) * np.sin(lats2) - np.sin(lats1) * np.cos(lats2) * np.cos(dLons)
    brng = np.arctan2(ys, xs)
    brng = brng * (180 / np.pi)
    brng = (brng + 360) % 360
    brng = 360 - brng
    return brng


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6373.0
    _lat1 = math.radians(lat1)
    _lon1 = math.radians(lon1)
    _lat2 = math.radians(lat2)
    _lon2 = math.radians(lon2)
    dlon = _lon2 - _lon1
    dlat = _lat2 - _lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(_lat1) * math.cos(_lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def ssi_dataframe(df, var1, var2):
    df_c = df.loc[(df[var1] != 0) & (df[var2] != 0), :]
    x_min = df_c.apply(lambda row: min(row[var1], row[var2]), axis=1)
    SSI = 2 * x_min.sum() / (df_c.loc[:, var1].sum() + df_c.loc[:, var2].sum())
    return SSI