import geopandas
import pandas
import regions
import os

shps = {
    "national": os.getcwd() + "/dbs/sampers/national/region.shp",
    "west": os.getcwd() + "/dbs/sampers/west/region.shp",
    "east": os.getcwd() + "/dbs/sampers/east/region.shp",
}

odms = {
    "national": os.getcwd() + "/dbs/sampers/national/trips.csv",
    "west":  os.getcwd() + "/dbs/sampers/west/trips.csv",
    "east": os.getcwd() + "/dbs/sampers/east/trips.csv",
}

bbox = {
    "national": regions.counties.to_crs("EPSG:3006"),
    "east": regions.counties[regions.counties['ID'].isin(['01', '03', '04', '09', '18', '19'])].to_crs('EPSG:3006'),
    "west": regions.counties[regions.counties['ID'].isin(['13', '14', '17'])].to_crs('EPSG:3006')
}


def read_shp(path):
    return geopandas.read_file(path).rename(columns={'te_csv_Bor': 'zone', 'K_vast': 'zone', 'K_samm': 'zone'})


def read_odm(path):
    return pandas.read_csv(path)

