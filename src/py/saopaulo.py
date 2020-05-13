import geopandas as gpd
import pandas as pd


metric_epsg = "EPSG:22523"

def zone_populations():
    sheet = pd.read_excel("../../dbs/saopaulo/population.xlsx", skiprows=6, index_col=0, skipfooter=17, sheet_name=0)
    census = sheet.dropna().reset_index('Zona ').rename(
        columns={'População': 'census_population', 'Zona ': 'zone'})
    census['zone'] = census['zone'].astype('int64')
    census = census.set_index('zone').census_population
    return zones().set_index('zone').join(census)

def zones():
    _zones = gpd.read_file('./../../dbs/saopaulo/zones/zones.shp')
    _zones = _zones.rename(columns={"NumeroZona": "zone"})[['zone', 'geometry']]
    return _zones


def boundary():
    return zones().assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")


def odm():
    odms = pd.read_excel("../../dbs/saopaulo/odm/odm.xlsx", skiprows=7, index_col=0, skipfooter=3).drop(columns="Total")
    assert odms.shape[0] == 517
    assert odms.shape[1] == 517
    odms = odms.stack()
    odms = odms / odms.sum()
    return odms
