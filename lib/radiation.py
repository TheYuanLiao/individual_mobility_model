from legacy import geostat
import sampers
import geopandas as gpd
import pandas as pd
import netherlands
import numpy as np
from rasterstats import zonal_stats


zones = {'sweden_east': sampers.shps['east'],
         'sweden_west': sampers.shps['west'],
         'sweden_national': sampers.shps['national'],
         'netherlands': netherlands.zones}


def grid_pop_load(mask):
    pop_grid = geostat.load(mask=mask).to_crs('EPSG:4326')
    return pop_grid


def get_pop(pop_grid, shp_n):
    # shp path or load function
    zone_p = zones[shp_n]

    # load spatial zones
    if 'sweden' in shp_n:
        regions = sampers.read_shp(zone_p).to_crs('EPSG:4326')
    else:
        regions = zone_p().to_crs('EPSG:4326')

    # get population in each sampers zone
    pop = gpd.sjoin(regions, pop_grid, how="inner", op='intersects')
    pop.drop_duplicates(subset=['GRD_ID'], inplace=True)
    pop = pop.set_index('zone', drop=True)
    pop = pop['population'].groupby(['zone']).sum().reset_index()
    regions = pd.merge(regions, pop, on='zone', how='outer')
    regions = regions.loc[regions['zone'] != 0, :]
    regions['population'].fillna(0, inplace=True)
    return regions


def get_pop_ssp(zs, shp_n, f='../../dbs/ssp2_total_2020.tif'):
    # shp path or load function
    zone_p = zs[shp_n]

    # load spatial zones
    if 'sweden' in shp_n:
        gdf_zs = sampers.read_shp(zone_p).to_crs('EPSG:4326')
    else:
        gdf_zs = zone_p().to_crs('EPSG:4326')
    results = zonal_stats(gdf_zs, f, stats=['sum'], geojson_out=True)
    zs_gdf_pz = gpd.GeoDataFrame.from_features(results)
    zs_dict = {row['zone']: row['sum'] for _, row in zs_gdf_pz.iterrows()}
    gdf_zs.loc[:, 'pop'] = gdf_zs['zone'].apply(lambda x: zs_dict[x])
    gdf_zs.loc[:, 'pop'] = gdf_zs.loc[:, 'pop'].fillna(0)
    return gdf_zs


def haversine_vec(data):
    # Convert to radians
    data = np.deg2rad(data)

    # Extract col-1 and 2 as latitudes and longitudes
    lat = data[:, 0]
    lng = data[:, 1]

    # Elementwise differentiations for latitudes & longitudes
    diff_lat = lat[:, None] - lat
    diff_lng = lng[:, None] - lng

    # Finally Calculate haversine
    d = np.sin(diff_lat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat) * np.sin(diff_lng / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(d))


def radiation(d, pop_array):
    def pij(i, j, d_matrix=d, pop_ary=pop_array):
        if i != j:
            ix = np.where(d_matrix[int(i), :] <= d_matrix[int(i), int(j)])
            return np.sum(pop_ary[ix]) - pop_ary[int(i)] - pop_ary[int(j)]
        else:
            return 0

    num_zone = len(pop_array)
    g = np.vectorize(pij)
    p = np.fromfunction(g, (num_zone, num_zone))
    pop_array = pop_array.reshape(num_zone, 1)
    pop = np.repeat(pop_array, num_zone, axis=1)  # Pi, Pop.T - Pj
    flows = pop * 1000 / (1 - pop / sum(pop_array)) * pop_array.dot(pop_array.T) / ((p + pop.T + pop) * (p + pop))
    return flows
