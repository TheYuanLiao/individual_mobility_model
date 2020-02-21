import pandas
import geopandas
import sqlite3


def load(location_name):
    conn = sqlite3.connect("../../dbs/sweden.sqlite3")
    df = pandas.read_sql_query("SELECT * FROM location WHERE type='home' and calc_name=?", params=[location_name], con=conn)
    geodf = geopandas.GeoDataFrame(
        df,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(df.longitude, df.latitude),
    )
    return geodf

