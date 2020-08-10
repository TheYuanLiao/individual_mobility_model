import geopandas as gpd


metric_epsg = "EPSG:3035"

def counties():
    return gpd.read_file('../dbs/alla_lan/alla_lan.shp')


def boundary():
    return counties().assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")
