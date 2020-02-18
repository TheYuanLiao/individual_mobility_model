import pandas as pd
from datetime import timedelta

temporal_treshold = timedelta(hours=12)


def from_dfs(df):
    """
    :type df: pandas.DataFrame
    """
    trips = []
    prev = None
    for _, row in df.iterrows():
        if prev is not None:
            diff = row.createdat - prev.createdat
            if diff < temporal_treshold:
                trips.append([
                    prev.userid,
                    prev.tweetid, row.tweetid,
                    prev.createdat, row.createdat,
                    prev.latitude, prev.longitude,
                    row.latitude, row.longitude,
                    diff,
                ])
        prev = row
    return pd.DataFrame(data=trips, columns=[
        "userid",
        "tweetid_o", "tweetid_d",
        "createdat_o", "createdat_d",
        "latitude_o", "longitude_o",
        "latitude_d", "longitude_d",
        "traveltime",
    ])
