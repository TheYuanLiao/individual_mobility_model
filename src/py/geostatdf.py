import pandas
import geopandas

shp_path = '../../dbs/geostat/grid/grid.shp'
pop_path = '../../dbs/geostat/population.csv'


def load(mask=None):
    population = pandas.read_csv(pop_path)
    shape = None
    if mask is not None:
        shape = geopandas.read_file(shp_path, mask=mask)
    else:
        shape = geopandas.read_file(shp_path)
    return shape.merge(population, on="GRD_ID")


def merge_home_location(geostatdf, homelocationdf):
    merged = geopandas.overlay(
        homelocationdf,
        geostatdf,
        how="intersection",
    )
    merged = merged.groupby('GRD_ID', as_index=False).count()[['GRD_ID', 'user_id']].rename(columns={'user_id': 'twitter_users'})
    return geostatdf.merge(merged, on='GRD_ID', how='right')
