import geopandas as gpd
import pandas as pd


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
