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


def aggregate_odm(df):
    origins = df.groupby('ozone', as_index=False).sum()[['ozone', 'total']].rename(
        columns={'ozone': 'zone', 'total': 'origin'})
    destinations = df.groupby('dzone', as_index=False).sum()[['dzone', 'total']].rename(
        columns={'dzone': 'zone', 'total': 'destination'})
    return origins.merge(destinations, on='zone')


def merge_odm_shp(odmdf, shpdf):
    return shpdf.merge(odmdf, on='zone')
