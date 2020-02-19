import pandas as pd

def from_trips(trips):
    gt = trips.groupby(['latitude_o', 'longitude_o', 'latitude_d', 'longitude_d'], as_index=False)
    gt = gt.count()[['latitude_o', 'longitude_o', 'latitude_d', 'longitude_d', 'userid']]
    return gt.rename(columns={'userid': 'count'})
