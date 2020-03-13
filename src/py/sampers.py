import geopandas
import pandas

shps = {
    "national": "./../../dbs/sampers/national/region.shp",
    "west": "./../../dbs/sampers/west/region.shp",
    "east": "./../../dbs/sampers/east/region.shp",
}

odms = {
    "national": "./../../dbs/sampers/national/trips.csv",
    "west":  "./../../dbs/sampers/west/trips.csv",
    "east": "./../../dbs/sampers/east/trips.csv",
}


def read_shp(path):
    return geopandas.read_file(path).rename(columns={'te_csv_Bor': 'zone', 'K_vast': 'zone', 'K_samm': 'zone'})


def read_odm(path):
    return pandas.read_csv(path)

