import geopandas


def convert_to_zones(latlonodm, clip_region, sampers_shp):
    odm_indexed = latlonodm.copy()
    odm_indexed.reset_index(inplace=True)
    odm_indexed.set_index('index')
    odm_indexed_2 = odm_indexed.copy()
    geo_orig = geopandas.GeoDataFrame(
        odm_indexed,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(odm_indexed.longitude_o, odm_indexed.latitude_o),
    )
    geo_dest = geopandas.GeoDataFrame(
        odm_indexed_2,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(odm_indexed_2.longitude_d, odm_indexed_2.latitude_d),
    )
    geo_orig = geopandas.clip(geo_orig, clip_region)
    geo_dest = geopandas.clip(geo_dest, clip_region)
    geo_orig = geo_orig.to_crs(sampers_shp.crs)
    geo_dest = geo_dest.to_crs(sampers_shp.crs)
    geo_orig_zone = geopandas.overlay(geo_orig, sampers_shp, how='intersection').set_index('index')
    geo_dest_zone = geopandas.overlay(geo_dest, sampers_shp, how='intersection').set_index('index')
    geo_combined = geo_orig_zone.join(geo_dest_zone, on='index', how='inner', rsuffix='_d')
    geo_combined = geo_combined.groupby(['zone', 'zone_d'], as_index=False)['count'].sum()
    return geo_combined.rename(columns={'zone': 'ozone', 'zone_d': 'dzone'})

