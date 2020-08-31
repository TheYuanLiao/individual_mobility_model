import geopandas as gpd
import pandas as pd


metric_epsg = "EPSG:28992"

counties = gpd.read_file('../../dbs/netherlands/provinces.shp').to_crs(metric_epsg)
municipalities = gpd.read_file('../../dbs/netherlands/gem_2017.shp').to_crs(metric_epsg)

def zones():
    _zones = gpd.read_file('../../dbs/netherlands/mobility_data/CBS_PC4_2017_v1.shp')
    _zones = _zones.rename(columns={"PC4": "zone"})[['zone', 'geometry']]
    return _zones


def boundary():
    return zones().assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")


def odm():
    sheet1 = pd.read_excel("../../dbs/netherlands/mobility_data/OViN2017_Databestand.xlsx")
    trips = sheet1[
        ['OPID', 'Wogem', 'Jaar', 'Maand', 'Dag', 'VerplID',
         'VertUur', 'VertPC', 'AankUur', 'AankPC', 'FactorV']]
    trips = trips.rename(columns={
        'Wogem': 'home_city',
        'Jaar': 'year',
        'Maand': 'month',
        'Dag': 'day',
        'VerplID': 'trip_id',
        'VertUur': 'origin_time',
        'VertPC': 'origin_zip',
        'AankUur': 'dest_time',
        'AankPC': 'dest_zip',
        'FactorV': 'weight_trip',
    })
    trips = trips.dropna(subset=['trip_id'])
    trips = trips.groupby(['OPID', 'trip_id']).apply(trip_row)
    trips['origin_zip'] = trips['origin_zip'].astype('int64')
    trips['dest_zip'] = trips['dest_zip'].astype('int64')
    odms = trips.groupby(['origin_zip', 'dest_zip']).sum()['weight_trip']
    z = zones().zone
    odms = odms.reindex(pd.MultiIndex.from_product([z, z]), fill_value=0)
    odms = odms / odms.sum()
    return odms


def trip_row(df):
    row = df.iloc[0]
    row['dest_zip'] = df.iloc[-1]['dest_zip']
    row['dest_time'] = df.iloc[-1]['dest_time']
    return row