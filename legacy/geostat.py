import pandas
import geopandas

shp_path = '../dbs/geostat/grid/grid.shp'
pop_path = '../dbs/geostat/population.csv'


def load(mask=None):
    population = pandas.read_csv(pop_path)
    shape = None
    if mask is not None:
        shape = geopandas.read_file(shp_path, mask=mask)
    else:
        shape = geopandas.read_file(shp_path)
    df = shape.merge(population, on="GRD_ID", how='left')
    # normalize column names
    df = df[["GRD_ID", "geometry", "TOT_P"]]
    df = df.rename(columns={"TOT_P": "population"})
    return df


def merge_home_location(geostatdf, homelocationdf):
    repartitioned = geopandas.overlay(
        homelocationdf,
        geostatdf,
        how="intersection",
    )
    df = repartitioned.groupby('GRD_ID', as_index=False).count()[['GRD_ID', 'user_id']]
    df = df.rename(columns={'user_id': 'population'})
    return geostatdf[['GRD_ID', 'geometry']].merge(df, on='GRD_ID', how='right')
