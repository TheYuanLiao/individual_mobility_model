import pandas as pd
from datetime import timedelta, timezone

temporal_treshold = timedelta(hours=12)

temporal_treshold_2 = timedelta(hours=48)


def from_dfs(df):
    """
    :type df: pandas.DataFrame
    """
    trips = []
    prev_loc = dict.fromkeys(df.userid)
    for _, row in df.iterrows():
        prev_user_loc = prev_loc[row.userid]
        if prev_user_loc is not None:
            diff = row.createdat - prev_user_loc.createdat
            if diff < temporal_treshold:
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

def from_dfs_with_morning_infer(df):
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
            if diff < temporal_treshold:
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
            elif diff < temporal_treshold_2 and row.createdat.replace(tzinfo=timezone.utc) > morning_infer:
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
