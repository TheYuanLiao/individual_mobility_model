import pandas as pd
import geopandas as gpd
import numpy as np
from datetime import timedelta, timezone
import sqlite3
from sklearn.cluster import DBSCAN


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
    df_or = df.shift(1).dropna().reset_index(drop=True)
    df_ds = df.shift(-1).dropna().reset_index(drop=True)
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
    "sweden": "./../../dbs/sweden/geotweets.csv",
}


def read_geotweets(region="sweden"):
    if region not in geotweet_paths:
        print("unknown region")
        return
    ts = pd.read_csv(geotweet_paths[region])
    ts["createdat"] = pd.to_datetime(ts.createdat, infer_datetime_format=True)
    return gpd.GeoDataFrame(
        ts,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(ts.longitude, ts.latitude),
    )


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


def trips_from_geotweets(df):
    """
    :type df: pandas.DataFrame
    """
    trips = []
    prev_loc = dict.fromkeys(df.userid)
    for _, row in df.iterrows():
        prev_user_loc = prev_loc[row.userid]
        if prev_user_loc is not None:
            diff = row.createdat - prev_user_loc.createdat
            if diff < timedelta(hours=12):
                trips.append([
                    row.userid,
                    prev_user_loc.tweetid, row.tweetid,
                    prev_user_loc.createdat, row.createdat,
                    prev_user_loc.latitude, prev_user_loc.longitude,
                    row.latitude, row.longitude,
                    diff,
                ])
        prev_loc[row.userid] = row
    return pd.DataFrame(data=trips, columns=[
        "userid",
        "tweetid_o", "tweetid_d",
        "createdat_o", "createdat_d",
        "latitude_o", "longitude_o",
        "latitude_d", "longitude_d",
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
    conn = sqlite3.connect('./../../dbs/' + db)
    df_raw = pd.read_sql_query("SELECT * FROM geo_tweet order by user_id", con=conn)
    return df_raw.rename(columns={
        'tweet_id': 'tweetid',
        'user_id': 'userid',
        'created_at': 'createdat',
        'hour_of_day': 'hourofday',
        'time_zone': 'timezone'
    })



