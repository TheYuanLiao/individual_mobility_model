import geopandas as gpd
import pandas as pd


def zones():
    return gpd.read_file('./../../dbs/saopaulo/zones/zones.shp')


def boundary():
    return zones().assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")
