import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import timedelta, timezone
import sqlite3
from sklearn.cluster import DBSCAN
import math
import os
import osmnx as ox


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


def cluster_groups(ts, min_samples=1):
    """
    Clusters each users regions with DBSCAN.
    :param ts:
    [userid*, latitude, longitude, region, ...rest]

    :param min_samples:
    min_samples parameter of DBSCAN.

    :return:
    [userid*, latitude, longitude, region, group ...rest]
    """

    def f(_ts):
        eps_km = len(_ts['region'].unique()) / 15
        kms_per_radian = 6371.0088
        coords_rad = np.radians(_ts[['latitude', 'longitude']].values)
        cls = DBSCAN(eps=eps_km / kms_per_radian, min_samples=min_samples, metric='haversine').fit(coords_rad)
        return _ts.assign(group=pd.Series(cls.labels_, index=_ts.index).values)

    groups = ts.groupby('userid', as_index=False).apply(f)
    return groups


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


def gaps(df):
    columns = ['createdat', 'region', 'label']
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


def remove_consecutive_region_visits(visits):
    def f(user_visits):
        user_visits.reset_index()
        prev_region = user_visits.shift(1).reset_index()[['region']]
        u_visits = user_visits.join(prev_region, rsuffix='_previous')
        return u_visits[u_visits['region'] != u_visits['region_previous']].reset_index(drop=True)

    visits_sorted = visits.reset_index().set_index(['userid', 'day', 'timeslot']).sort_index().reset_index()
    return visits_sorted.groupby('userid').apply(f).reset_index(level=1, drop=True).drop(
        columns='region_previous').set_index('userid')


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


def read_geotweets(region="sweden"):
    if region not in geotweet_paths:
        print("unknown region")
        return
    return read_geotweets_raw(geotweet_paths[region])


def latlngodm_from_trips(trips):
    gt = trips.groupby(['latitude_o', 'longitude_o', 'latitude_d', 'longitude_d'], as_index=False)
    gt = gt.count()[['latitude_o', 'longitude_o', 'latitude_d', 'longitude_d', 'userid']]
    return gt.rename(columns={'userid': 'count'})


def latlngodm_to_sampersodm(latlonodm, clip_region, sampers_shp):
    odm_indexed = latlonodm.copy()
    odm_indexed.reset_index(inplace=True)
    odm_indexed.set_index('index')
    odm_indexed_2 = odm_indexed.copy()
    geo_orig = gpd.GeoDataFrame(
        odm_indexed,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(odm_indexed.longitude_o, odm_indexed.latitude_o),
    )
    geo_dest = gpd.GeoDataFrame(
        odm_indexed_2,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(odm_indexed_2.longitude_d, odm_indexed_2.latitude_d),
    )
    geo_orig = gpd.clip(geo_orig, clip_region)
    geo_dest = gpd.clip(geo_dest, clip_region)
    geo_orig = geo_orig.to_crs(sampers_shp.crs)
    geo_dest = geo_dest.to_crs(sampers_shp.crs)
    geo_orig_zone = gpd.overlay(geo_orig, sampers_shp, how='intersection').set_index('index')
    geo_dest_zone = gpd.overlay(geo_dest, sampers_shp, how='intersection').set_index('index')
    geo_combined = geo_orig_zone.join(geo_dest_zone, on='index', how='inner', rsuffix='_d')
    geo_combined = geo_combined.groupby(['zone', 'zone_d'], as_index=False)['count'].sum()
    return geo_combined.rename(columns={'zone': 'ozone', 'zone_d': 'dzone'})


def rescale_population(populationdf):
    populationdf['population_normal'] = populationdf['population'] / populationdf['population'].max()
    populationdf['population_pow'] = populationdf['population_normal'] ** 2
    return populationdf


def trips_from_geotweets(df, threshold=None):
    """
    :type df: pandas.DataFrame
    """
    df_copy = df.copy(deep=True).reset_index()
    trips = []
    delta_thres = None
    if threshold is not None:
        delta_thres = timedelta(hours=threshold)
    prev_loc = dict.fromkeys(df_copy['userid'].unique())
    for _, row in df.iterrows():
        prev_user_loc = prev_loc[row.name]
        if prev_user_loc is not None:
            diff = row['createdat'] - prev_user_loc['createdat']
            if delta_thres is None or diff < delta_thres:
                trips.append([
                    row.name,
                    prev_user_loc['tweetid'], row['tweetid'],
                    prev_user_loc['createdat'], row['createdat'],
                    prev_user_loc['timezone'], row['timezone'],
                    prev_user_loc['latitude'], prev_user_loc['longitude'],
                    row['latitude'], row['longitude'],
                    prev_user_loc['region'], row['region'],
                    prev_user_loc['label'], row['label'],
                    diff,
                ])
        prev_loc[row.name] = row
    return pd.DataFrame(data=trips, columns=[
        "userid",
        "tweetid_o", "tweetid_d",
        "createdat_o", "createdat_d",
        "timezone_o", "timezone_d",
        "latitude_o", "longitude_o",
        "latitude_d", "longitude_d",
        "region_o", "region_d",
        "label_o", "label_d",
        "traveltime",
    ])


def trips_from_geotweets_morning_infer(df):
    """
    :type df: pandas.DataFrame
    """
    trips = []
    prev_loc = dict.fromkeys(df.userid)
    prev_made_trip = dict.fromkeys(df.userid)
    for _, row in df.iterrows():
        prev_user_loc = prev_loc[row.userid]
        if prev_user_loc is not None:
            diff = row.createdat - prev_user_loc.createdat
            morning_infer = row.createdat.replace(tzinfo=timezone.utc, hour=6)
            if diff < timedelta(hours=12):
                trips.append([
                    row.userid,
                    prev_user_loc.tweetid, row.tweetid,
                    prev_user_loc.createdat, row.createdat,
                    prev_user_loc.latitude, prev_user_loc.longitude,
                    row.latitude, row.longitude,
                    diff,
                    "12h"
                ])
                prev_made_trip[row.userid] = True
            elif diff < timedelta(hours=48) and row.createdat.replace(tzinfo=timezone.utc) > morning_infer:
                trips.append([
                    prev_user_loc.userid,
                    None, row.tweetid,
                    morning_infer, row.createdat,
                    prev_user_loc.latitude, prev_user_loc.longitude,
                    row.latitude, row.longitude,
                    diff,
                    "infered"
                ])
                prev_made_trip[row.userid] = True
            elif prev_made_trip[row.userid]:
                trips.append([
                    prev_user_loc.userid,
                    prev_user_loc.tweetid, None,
                    prev_user_loc.createdat, None,
                    prev_user_loc.latitude, prev_user_loc.longitude,
                    None, None,
                    diff,
                    "missed"
                ])
                prev_made_trip[row.userid] = False
        prev_loc[row.userid] = row
    return pd.DataFrame(data=trips, columns=[
        "userid",
        "tweetid_o", "tweetid_d",
        "createdat_o", "createdat_d",
        "latitude_o", "longitude_o",
        "latitude_d", "longitude_d",
        "traveltime",
        "type"
    ])


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


def travel_survey_str_timestamp_to_datetime(time_column):
    def fn(row):
        d = pd.to_datetime(row['date'])
        timestr = str(int(row[time_column]))
        if len(timestr) > 2:
            hour, minute = timestr[:-2], timestr[-2:]
            d = d.replace(hour=int(hour), minute=int(minute))
            return d
        else:
            d = d.replace(hour=0, minute=int(timestr))
            return d
        print(timestr)

    return fn


def travel_survey_trips_clean(df):
    # purpose
    df = df.dropna(subset=['purpose'])
    df = df.assign(purpose=df['purpose'].astype(int))
    pmap = pd.read_excel("../../dbs/Swedish National Travel Survey (2011-2016)/variable_values.xlsx",
                         sheet_name="purpose")
    pmap = pmap.rename(columns={'value': 'purpose'})
    df = df.merge(pmap, on='purpose').rename(columns={'meaning': 'purpose_meaning'})
    # timestamps
    df = df.dropna(subset=['desti_main_time', 'origin_main_time'])
    df = df.assign(
        origin_time=df[['date', 'origin_main_time']].apply(travel_survey_str_timestamp_to_datetime('origin_main_time'),
                                                           axis=1))
    df = df.assign(destination_time=df[['date', 'desti_main_time']].apply(
        travel_survey_str_timestamp_to_datetime('desti_main_time'), axis=1))
    return df


def spssim(X=None, Y=None, D=None, nquantiles=20):
    """
    Calculate SpSSIM score between X and Y, using the distances from D.
    X,Y,D must all be a pd.Series with the same MultiIndex (origin zone, destination zone).
    X,Y must be normalized before calling this function.
    """
    if not Y.index.equals(X.index):
        raise Exception('Y does not have same index as X')
    if not D.index.equals(Y.index):
        raise Exception('D does not have same index as Y')
    if np.abs(np.sum(X) - 1) > 1e-5:
        raise Exception('X is not normalized')
    if np.abs(np.sum(Y) - 1) > 1e-5:
        raise Exception('Y is not normalized')
    # Define C1 and C2 using Twitter OD as suggested by Pollard et al. (2013)
    C1, C2 = Y.mean() ** 2 * 1e-4, Y.var() * 1e-2

    Wx = X.unstack().values
    Wy = Y.unstack().values
    # Compute the quantiles.
    quantiles = pd.qcut(D, q=nquantiles)
    qgrps = quantiles.groupby(quantiles)
    quantile_scores = []
    # Create spatial weight matrix initialized to 0.
    # This will be reused between quantiles because stacking/unstacking 9M cell matrix takes time (~3s)
    spatial_weight = pd.Series(index=quantiles.index, dtype=int).unstack().values
    for grpkey in qgrps.groups:
        # Update spatial weight matrix such that each of the zones in this quantile == 1.
        np.put(spatial_weight, qgrps.indices[grpkey], 1)
        wx = (Wx * spatial_weight).flatten()
        wy = (Wy * spatial_weight).flatten()
        # Set trip weight
        trip_weight = wx.sum()
        # Reset spatial weight matrix to previous value, in order to reuse.
        np.put(spatial_weight, qgrps.indices[grpkey], 0)
        score = (2 * wx.mean() * wy.mean() + C1) * (2 * np.cov(wx, wy)[0][1] + C2) / (
                (wx.mean() ** 2 + wy.mean() ** 2 + C1) * (wx.var() + wy.var() + C2))
        quantile_scores.append([
            grpkey,  # quantile
            score,  # score
            wx.sum(),  # sampers_weight
            wx.mean(),  # sampers_mean
            wx.var(),  # sampers_var
            wy.sum(),  # twitter_weight
            wy.mean(),  # twitter_mean
            wy.var(),  # twitter_var
            np.cov(wx, wy)[0][1]  # covariance
        ])
    return pd.DataFrame(
        quantile_scores,
        columns=[
            'quantile',
            'score',
            'sampers_weight',
            'sampers_mean',
            'sampers_var',
            'twitter_weight',
            'twitter_mean',
            'twitter_var',
            'covariance',
        ],
    ).set_index('quantile')


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
