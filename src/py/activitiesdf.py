import pandas as pd
import geopandas as gpd

regions = {
    "sweden": "./../../dbs/activities/sweden.csv",
}


def read_csv(region="sweden"):
    if region not in regions:
        print("unknown region")
        return
    acts = pd.read_csv(regions[region])
    acts["createdat"] = pd.to_datetime(acts.createdat, format="%Y-%m-%d %H:%M:%S%z")
    return gpd.GeoDataFrame(
        acts,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(acts.longitude, acts.latitude),
    )


def during_home(df):
    weekdays = (df['weekday'] < 6) & (0 < df['weekday'])
    weekends = (df['weekday'] == 6) | (0 == df['weekday'])
    morning_evening = (df['hourofday'] < 10) | (17 < df['hourofday'])
    return df[((weekdays) & (morning_evening)) | (weekends)]


def label_home(df):
    print("copying")
    dfc = df.copy(deep=True)
    print("reindex")
    dfc = dfc.set_index(['userid', 'region', 'tweetid']).sort_index()
    print("largest cluster")
    homeidx = during_home(dfc)\
        .groupby(['userid', 'region']).size() \
        .groupby('userid').nlargest(1) \
        .index.tolist()
    print(len(homeidx))
    print("set values")
    for (_, userid, regionid) in homeidx:
        dfc.loc[(userid, regionid), 'label'] = "home"
    return dfc


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
        home_region = udf[udf['label'] == 'home'].iloc[0]['region']
        workidxs = during_work(udf)\
            .groupby(['region']).size().nlargest(2) \
            .index.tolist()
        if len(workidxs) == 1 and workidxs[0] == home_region:
            print("find work place: not enough visits")
            continue
        workidx = workidxs[0] if workidxs[0] != home_region else workidxs[1]
        dfc.loc[(uid, workidx), 'label'] = "work"
        i += 1
        if i % 100 == 0:
            print("done with {}".format(i))
    return dfc


def plot_label_distrib(region_df):
    region_df.groupby(['quantile', 'label']).size() \
        .unstack().fillna(0) \
        .plot(kind='barh', stacked=True, figsize=(15, 7))


def plot_label_hourofday(region_df):
    region_df.groupby(['hourofday', 'label']).size() \
        .unstack().fillna(0) \
        .plot(kind='line', figsize=(15, 7))


def gaps(df):
    columns = ['createdat', 'region']
    df_or = df.shift(1).dropna()[columns].reset_index()
    df_ds = df.shift(-1).dropna()[columns].reset_index()
    df = df_or.join(df_ds, lsuffix="_origin", rsuffix="_destination")
    df = df.assign(duration=df['createdat_destination'] - df['createdat_origin'])
    return df
