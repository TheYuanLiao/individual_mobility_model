import os
import subprocess
import yaml
import sqlite3
from sqlalchemy import create_engine
import pandas as pd
import multiprocessing as mp
from tzwhere import tzwhere
from dateutil import tz
from datetime import datetime as dt
tzg = tzwhere.tzwhere()


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__')) # os.getcwd()
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()

with open(ROOT_dir + '/lib/regions.yaml') as f:
    region_manager = yaml.load(f, Loader=yaml.FullLoader)


def where_self(row):
    """
    Get the time zone from a pair of GPS coordinates.
    :param row: contains "latitude" and "longitude"
    :type row: a row of a dataframe
    :return: a timezone corresponding to the input coordinates pair
    :rtype: string
    """
    try:
        x = tz.gettz(tzg.tzNameAt(row["latitude"], row["longitude"]))
    except:
        x = "Unknown"
    return x


def where2time(row):
    """
    Convert UTC time to local time with known time zone.
    :param row: contains "UTC", "time_zone", "created_at"
    :type row: a row of a dataframe
    :return: local time converted from UTC and time_zone
    :rtype: object
    """
    from_zone = tz.gettz('UTC')
    timezone = row["time_zone"]

    rawUTC = dt.strptime(row["created_at"],'%b %d %H:%M:%S %Y')
    utc = rawUTC.replace(tzinfo=from_zone)
    central = str(utc.astimezone(timezone))
    rawT = dt.strptime(central[:-6], '%Y-%m-%d %H:%M:%S')
    return rawT


def region_converter(region=None):
    """
    Convert time of raw geotagged tweets and save to a new db per specified region.
    :param region: name of the region to be processed
    :type region: string
    :return: none
    :rtype: none
    """
    if not os.path.exists(ROOT_dir + f'/dbs/{region}/{region}.sqlite3'):
        db = region_manager[region]['source_path']
        conn = sqlite3.connect(db)
        df_raw = pd.read_sql_query("SELECT * FROM geo INNER JOIN records ON geo.rec_id = records.id", con=conn)
        df_raw = df_raw.loc[:, ['tw_id', 'user_id', 'time',
                                'coord_lat', 'coord_long']].rename(columns={'tw_id': 'tweet_id',
                                                                            'time': 'created_at',
                                                                            'coord_lat': 'latitude',
                                                                            'coord_long': 'longitude'})
        print(f'Region {region} data retrieved.')
        # Get time zone and convert the UTC time into local time
        df_raw["time_zone"] = df_raw.apply(lambda row: where_self(row), axis=1)
        df_raw = df_raw.loc[df_raw["time_zone"] != "Unknown", :]
        df_raw["created_at"] = df_raw.apply(lambda row: where2time(row), axis=1)
        df_raw["time_zone"] = df_raw["time_zone"].apply(lambda x: str(x)[8:-2])
        df_raw.loc[:, 'month'] = df_raw.loc[:, 'created_at'].apply(lambda x: x.month)
        df_raw.loc[:, 'weekday'] = df_raw.loc[:, 'created_at'].apply(lambda x: x.weekday())
        df_raw.loc[:, 'hour_of_day'] = df_raw.loc[:, 'created_at'].apply(lambda x: x.hour)
        df_raw = df_raw.loc[df_raw['time_zone'] != '']
        print(f'Region {region} time processed.')

        # Save into a new .sqlite3
        if not os.path.exists(ROOT_dir + f'/dbs/{region}/'):
            os.makedirs(ROOT_dir + f'/dbs/{region}/')

        engine = create_engine('sqlite:///' + ROOT_dir + f'/dbs/{region}/{region}.sqlite3', echo=False)
        sqlite_connection = engine.connect()
        sqlite_table = 'geo_tweet'
        df_raw.to_sql(sqlite_table, sqlite_connection, if_exists='replace', index=False)
        sqlite_connection.close()
        print(f'Region {region} converted .sqlite3 saved.')
    else:
        print(f'Region {region} converted .sqlite3 exists!')


if __name__ == '__main__':
    region_list = ['sweden', 'netherlands', 'saopaulo', 'australia', 'austria', 'barcelona',
                   'capetown', 'cebu', 'egypt', 'guadalajara', 'jakarta',
                   'johannesburg', 'kualalumpur', 'lagos', 'madrid', 'manila', 'mexicocity', 'moscow', 'nairobi',
                   'rio', 'saudiarabia', 'stpertersburg', 'surabaya']

    # parallelize the converting of tweets of multiple regions
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(region_converter, [(r, ) for r in region_list])
    pool.close()
