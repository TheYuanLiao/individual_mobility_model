import pandas as pd
import geopandas as gpd
from datetime import timedelta

def during_work(df):
    weekdays = (df['weekday'] < 6) & (0 < df['weekday'])
    business_hours = (df['hourofday'] > 6) | (19 > df['hourofday'])
    return df[((weekdays) & (business_hours))]


def label_work(df):
    dfc = df.copy(deep=True)
    i = 0
    for uid in dfc.index.get_level_values(0).unique():
        udfc = dfc.loc[uid, :]
        udf = udfc.copy(deep=True).reset_index()
        home_regions = udf[udf['label'] == 'home']['region'].unique().tolist()
        workidxs = during_work(udf)\
            .groupby(['region']).size().nlargest(4) \
            .index.tolist()
        for homeidx in home_regions:
            if homeidx in workidxs:
                workidxs.remove(homeidx)
        if len(workidxs) == 0:
            print("find work place: not enough visits")
            continue
        else:
            dfc.loc[(uid, workidxs[0]), 'label'] = "work"
        i += 1
        if i % 100 == 0:
            print("done with {}".format(i))
    return dfc

def during_home(df):
    weekdays = (df['weekday'] < 6) & (0 < df['weekday'])
    weekends = (df['weekday'] == 6) | (0 == df['weekday'])
    morning_evening = (df['hourofday'] < 9) | (18 < df['hourofday'])
    return df[((weekdays) & (morning_evening)) | (weekends)]


def home_overlaps(h1, h2):
    return h1['home_start'] < h2['home_end'] and h2['home_start'] < h1['home_end']

def less_than_30_days(h):
    return (h['home_end'] - h['home_start']) < timedelta(days=30)

def label_multiple_homes(df):
    print("copying")
    acts_2 = df.copy(deep=True).reset_index()
    print("reindex")
    acts_2 = acts_2.set_index(['userid', 'region', 'tweetid']).sort_index()
    print("largest cluster")
    homeidx = during_home(acts_2) \
        .groupby(['userid', 'region']).size() \
        .groupby('userid').nlargest(3)
    homeidx.index = homeidx.index.droplevel()
    usr_3homeloc = acts_2.reset_index().set_index(['userid', 'region']).loc[homeidx.index.values]
    usr_3homeloc = usr_3homeloc.reset_index().set_index(['userid', 'region']).sort_index()
    home_start = pd.Series(index=homeidx.index, dtype='datetime64[ns]')
    home_end = pd.Series(index=homeidx.index, dtype='datetime64[ns]')
    for (u, r), size in homeidx.iteritems():
        perc_10 = int(size / 10)
        if size < 10:
            hometweets = usr_3homeloc.loc[(u, r)]
        else:
            hometweets = usr_3homeloc.loc[(u, r)].iloc[perc_10:-perc_10]
        home_start.loc[(u, r)] = hometweets['createdat'].min()
        home_end.loc[(u, r)] = hometweets['createdat'].max()
    homes = pd.DataFrame({'size': homeidx, 'home_start': home_start, 'home_end': home_end})
    for u, rows in homes.groupby(level=0):
        hs = rows.sort_values('size', ascending=False)
        if len(hs) < 2:
            continue
        if home_overlaps(hs.iloc[0], hs.iloc[1]) or less_than_30_days(hs.iloc[1]):
            homes.drop(index=[hs.iloc[1].name], inplace=True)
        if len(hs) < 3:
            continue
        if home_overlaps(hs.iloc[0], hs.iloc[2]) or home_overlaps(hs.iloc[1], hs.iloc[2]) or less_than_30_days(
                hs.iloc[2]):
            homes.drop(index=[hs.iloc[2].name], inplace=True)
    homes = homes.dropna()
    homes_list = homes.index.tolist()
    print("set values")
    for (userid, regionid) in homes_list:
        acts_2.loc[(userid, regionid), 'label'] = "home"
    return acts_2

def latest_home(h1, h2):
    return (h1 if h1['home_start'] > h2['home_start'] else h2)

def label_current_home(df_input):
    print("copying")
    df = df_input.copy(deep=True).reset_index()
    print("reindex")
    df = df.set_index(['userid', 'region', 'tweetid']).sort_index()
    print("largest cluster")
    homeidx = during_home(df) \
        .groupby(['userid', 'region']).size() \
        .groupby('userid').nlargest(3)
    homeidx.index = homeidx.index.droplevel()
    usr_3homeloc = df.reset_index().set_index(['userid', 'region']).loc[homeidx.index.values]
    usr_3homeloc = usr_3homeloc.reset_index().set_index(['userid', 'region']).sort_index()
    home_start = pd.Series(index=homeidx.index, dtype='datetime64[ns]')
    home_end = pd.Series(index=homeidx.index, dtype='datetime64[ns]')
    for (u, r), size in homeidx.iteritems():
        perc_10 = int(size / 10)
        if size < 10:
            hometweets = usr_3homeloc.loc[(u, r)]
        else:
            hometweets = usr_3homeloc.loc[(u, r)].iloc[perc_10:-perc_10]
        home_start.loc[(u, r)] = hometweets['createdat'].min()
        home_end.loc[(u, r)] = hometweets['createdat'].max()
    homes = pd.DataFrame({'size': homeidx, 'home_start': home_start, 'home_end': home_end})
    home_indexes = []
    for u, rows in homes.groupby(level=0):
        hs = rows.sort_values('size', ascending=False)
        current_home = hs.iloc[0]
        if len(hs) > 1:
            if not (home_overlaps(hs.iloc[0], hs.iloc[1]) or less_than_30_days(hs.iloc[1])):
                current_home = latest_home(current_home, hs.iloc[1])
        if len(hs) > 2:
            if not (home_overlaps(hs.iloc[0], hs.iloc[2]) or home_overlaps(hs.iloc[1], hs.iloc[2]) or less_than_30_days(hs.iloc[2])):
                current_home = latest_home(current_home, hs.iloc[2])
        home_indexes.append(current_home.name)
    print("set values")
    for (userid, regionid) in home_indexes:
        df.loc[(userid, regionid), 'label'] = "home"
    return df



def aggregate_odm(df):
    origins = df.groupby('ozone', as_index=False).sum()[['ozone', 'total']].rename(
        columns={'ozone': 'zone', 'total': 'origin'})
    destinations = df.groupby('dzone', as_index=False).sum()[['dzone', 'total']].rename(
        columns={'dzone': 'zone', 'total': 'destination'})
    return origins.merge(destinations, on='zone')


def merge_odm_shp(odmdf, shpdf):
    return shpdf.merge(odmdf, on='zone')


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