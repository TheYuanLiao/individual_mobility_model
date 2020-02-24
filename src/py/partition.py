import geopandas

def sampers_odm_from_latlon_odm(latlonodm, clip_region, sampers_shp):
    latlonodm.reset_index(inplace=True)
    latlonodm.set_index('index')
    latlonodm_2 = latlonodm.copy()
    geo_orig = geopandas.GeoDataFrame(
        latlonodm,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(latlonodm.longitude_o, latlonodm.latitude_o),
    )
    geo_dest = geopandas.GeoDataFrame(
        latlonodm_2,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(latlonodm_2.longitude_d, latlonodm_2.latitude_d),
    )
    geo_orig = geopandas.clip(geo_orig, clip_region)
    geo_dest = geopandas.clip(geo_dest, clip_region)
    geo_orig = geo_orig.to_crs(sampers_shp.crs)
    geo_dest = geo_dest.to_crs(sampers_shp.crs)
    geo_orig_zone = geopandas.overlay(geo_orig, sampers_shp, how='intersection').set_index('index')
    geo_dest_zone = geopandas.overlay(geo_dest, sampers_shp, how='intersection').set_index('index')
    geo_combined = geo_orig_zone.join(geo_dest_zone, on='index', how='inner', rsuffix='_d')
    odm = geo_combined.groupby(['zone', 'zone_d'], as_index=False).sum()[['zone', 'zone_d', 'count']]
    return odm
