from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import numpy as np
import pandas as pd
import geopandas as gpd
import sqlite3
import activitiesdf

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

def cluster_tweets(df, eps_km=0.1, min_samples=1):
    kms_per_radian = 6371.0088
    coords = df[['latitude', 'longitude']].values
    return DBSCAN(eps=eps_km/kms_per_radian, min_samples=min_samples, metric='haversine').fit(np.radians(coords))


def cluster_spatial(tws, eps_km=0.1, min_samples=1):
    cls = cluster_tweets(tws, eps_km=eps_km, min_samples=min_samples)
    labels = pd.Series(cls.labels_)
    return tws.assign(region=pd.Series(cls.labels_, index=tws.index).values)

def cluster(tweets):
    regions = tweets.groupby('userid', as_index=False).apply(cluster_spatial)
    return regions

def get_home_locations(tweets):
    tweets['createdat'] = pd.to_datetime(tweets.createdat, utc=True)
    tweets['label'] = 'other'
    tweets_w_home = activitiesdf.label_current_home(tweets)
    home_locations = tweets_w_home[tweets_w_home['label'] == 'home'].reset_index().groupby(['userid', 'region']).first().reset_index()
    return gpd.GeoDataFrame(
        home_locations,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(home_locations.longitude, home_locations.latitude)
    ), tweets_w_home

def get_user_from_region(home_locations, region):
    countries = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    sweden = countries[countries.name == region]
    return gpd.clip(home_locations, sweden).set_index('userid').index