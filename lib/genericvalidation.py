from sklearn.metrics import pairwise_distances
import pandas as pd
import geopandas as gpd
import mscthesis


def zone_distances(zones):
    """
    :param zones
    GeoDataFrame [*index, zone, geometry]
    Must be in a CRS of unit: metre
    """
    for ax in zones.crs.axis_info:
        assert ax.unit_name == 'metre'

    print("Calculating distances between zones...")
    distances_meters = pairwise_distances(
        list(zip(
            zones.geometry.centroid.x.to_list(),
            zones.geometry.centroid.y.to_list(),
        ))
    )
    distances = pd.DataFrame(
        distances_meters / 1000,
        columns=zones.zone,
        index=zones.zone,
    ).stack()
    return distances


def distance_quantiles(zone_dist):
    print("Calculating quantiles...")
    quantiles = pd.qcut(zone_dist, q=100)
    qgrps = quantiles.groupby(quantiles)
    return qgrps


def crs_convert_visits(visits, zones):
    print("Convering visits to zone CRS")
    visits = gpd.GeoDataFrame(
        visits,
        crs="EPSG:4326",
        geometry=gpd.points_from_xy(visits.longitude, visits.latitude),
    )
    return visits.to_crs(zones.crs)


def align_visits_to_zones(visits, zones):
    print("Aligning region-visits to zones...")
    regional_visits = visits[visits.kind == 'region']
    n_regional_visits_before = regional_visits.shape[0]
    user_regions = regional_visits.groupby(['userid', 'region']).head(1)
    user_zones = gpd.sjoin(user_regions, zones, op='intersects')[['region', 'zone']]
    regional_visits = user_zones.merge(regional_visits, on=['userid', 'region'])
    print("removed", n_regional_visits_before - regional_visits.shape[0], "region-visits due to missing zone geom")

    print("Aligning point-visits to zones...")
    point_visits = visits[visits.kind == 'point']
    if point_visits.shape[0] > 0:
        n_point_visits_before = point_visits.shape[0]
        point_visits = gpd.sjoin(point_visits, zones, op='intersects')
        print("removed", n_point_visits_before - point_visits.shape[0], "point-visits due to missing zone geom")
    else:
        point_visits = point_visits.assign(zone='0')

    # Recombine
    columns = ['day', 'timeslot', 'zone']
    # Special handling of created at in order to have baseline and baseline 24h time threshold.
    if 'createdat' in visits:
        columns.append('createdat')

    visits = pd.concat([
        regional_visits[columns],
        point_visits[columns]
    ])
    print(visits.shape[0], "visits left after alignment")
    # Re-sort to chronological order
    visits = visits \
        .reset_index().set_index(['userid', 'day', 'timeslot']).sort_index() \
        .reset_index().set_index('userid')

    return visits


def aligned_visits_to_odm(visits, multiindex, timethreshold_hours=None):
    print("Creating odm...")
    gaps_columns = ['zone']

    if "createdat" in visits:
        gaps_columns.append("createdat")

    gaps = mscthesis.visit_gaps(visits[gaps_columns])
    if timethreshold_hours is not None:
        print("Applying timethreshold to gaps [{} hours]...".format(timethreshold_hours))
        gaps = gaps.assign(duration=gaps.createdat_destination - gaps.createdat_origin)
        gaps = gaps[gaps.duration < pd.Timedelta(timethreshold_hours, "hours")]

    gaps = gaps[['zone_origin', 'zone_destination']]
    sparse_odm = gaps \
        .groupby(['zone_origin', 'zone_destination']).size() \
        .reindex(multiindex, fill_value=0.0)
    sparse_odm = sparse_odm / sparse_odm.sum()
    return sparse_odm


def visits_to_odm(visits, zones, timethreshold_hours=None):
    crs_visits = crs_convert_visits(visits, zones)
    aligned_visits = align_visits_to_zones(crs_visits, zones)
    odm = aligned_visits_to_odm(
        aligned_visits,
        pd.MultiIndex.from_product([
            zones.zone.tolist(),
            zones.zone.tolist(),
        ]),
        timethreshold_hours,
    )
    return odm
