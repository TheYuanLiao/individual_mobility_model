import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.metrics import pairwise_distances
import sampers
import mscthesis

scales = ['national', 'east', 'west']


class Sampers:
    def __init__(self):
        self.zones = dict()
        self.distances = dict()
        self.odm = dict()

    def prepare(self):
        for scale in scales:
            print("Preparing scale", scale)
            print("Reading original data...")
            zones = sampers.read_shp(sampers.shps[scale])
            odm = sampers.read_odm(sampers.odms[scale]).set_index(['ozone', 'dzone'])['total']
            print("zones", zones.shape)
            print("odm", odm.shape, odm.sum())

            # ODM file can contain trips between zones that are not actually part of the scale.
            # Drop trips between unknown zones and
            # insert 0.0 trips between zones that are not represented in ODM
            print("Reindexing...")
            zonesx = zones.set_index('zone')
            odm = odm.reindex(
                pd.MultiIndex.from_product([
                    zonesx.index,
                    zonesx.index,
                ]),
                fill_value=0.0,
            )
            print("odm", odm.shape)
            odm = odm / odm.sum()

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
            ).stack().reindex(odm.index)
            print("distances", distances.shape)

            if scale == "national":
                odm[distances < 100] = 0
                odm = odm / odm.sum()

            self.zones[scale] = zones
            self.distances[scale] = distances
            self.odm[scale] = odm
            print()

    def convert(self, visits):
        """

        :param visits:
        pd.DataFrame (userid*, day, timeslot, kind, region, latitude, longitude)
        latitude and longitude should be in CRS EPSG:4326

        """
        print("Converting visits to GeoDataFrame...")
        visits = gpd.GeoDataFrame(
            visits,
            crs="EPSG:4326",
            geometry=gpd.points_from_xy(visits.longitude, visits.latitude),
        )
        print("Converting CRS...")
        # all zones share CRS so does not matter which is chosen
        return visits.to_crs(self.zones["national"].crs)

    def align(self, scale, visits, home_locations):
        """
        Align visits in regards to a specific Sampers zone.

        :param scale:
        one of ['national', 'east', 'west']

        :param visits:
        visits as returned from `convert`

        :param home_locations:
        gpd.GeoDataFrame(userid*, geometry) in CRS EPSG:3006

        :return:
        Sparse ODM aligned to the Sampers zones on this scale
        """
        # Remove users not in sampling zone
        if scale not in sampers.bbox:
            print("Not bboxing", scale)
        else:
            assert home_locations.crs == sampers.bbox[scale].crs
            n_visits_before = visits.shape[0]
            home_locations_in_sampling = gpd.sjoin(home_locations, sampers.bbox[scale])
            visits = visits[visits.index.isin(home_locations_in_sampling.index)]
            print("removed", n_visits_before - visits.shape[0], "visits due to sampling bbox")

        print("Aligning region-visits to Sampers zones...")
        regional_visits = visits[visits.kind == 'region']
        n_regional_visits_before = regional_visits.shape[0]
        user_regions = regional_visits.groupby(['userid', 'region']).head(1)
        user_zones = gpd.sjoin(user_regions, self.zones[scale], op='intersects')[['region', 'zone']]
        regional_visits = user_zones.merge(regional_visits, on=['userid', 'region'])
        print("removed", n_regional_visits_before - regional_visits.shape[0], "region-visits due to missing zone geom")

        print("Aligning point-visits to Sampers zones...")
        point_visits = visits[visits.kind == 'point']
        n_point_visits_before = point_visits.shape[0]
        point_visits = gpd.sjoin(point_visits, self.zones[scale], op='intersects')
        print("removed", n_point_visits_before - point_visits.shape[0], "point-visits due to missing zone geom")

        # Recombine
        visits = pd.concat([
            regional_visits[['day', 'timeslot', 'zone']],
            point_visits[['day', 'timeslot', 'zone']]
        ])
        print(visits.shape[0], "visits left after alignment")
        # Re-sort to chronological order
        visits = visits \
            .reset_index().set_index(['userid', 'day', 'timeslot']).sort_index() \
            .reset_index().set_index('userid')

        print("Creating ODM...")
        sparse_odm = mscthesis.visit_gaps(visits[['zone']]) \
            .groupby(['zone_origin', 'zone_destination']).size() \
            .reindex(self.odm[scale].index, fill_value=0.0)

        sparse_odm = sparse_odm / sparse_odm.sum()
        return sparse_odm

    def distance_cut(self, scale, odm):
        if scale == 'national':
            odm[self.distances[scale] < 100] = 0

        return odm / odm.sum()


class GravityModel:
    def __init__(self, beta=0.03, max_iter=5000, tolerance=1e-8):
        """
        :param beta:
        Beta parameter to gravity model. Should be positive.
        """
        self.beta = beta
        self.max_iter = max_iter
        self.tolerance=tolerance

    def describe(self):
        return {
            "beta": self.beta,
            "max_iter": self.max_iter,
            "tolerance": self.tolerance,
        }

    def seed(self, distances):
        return np.exp(-self.beta * distances)

    def gravitate(self, sparse_odm, seed):
        """
        :param sparse_odm
        Estimated travel demand between zones.
        Must be a pd.Series with MultiIndex (origin zone, destination zone).

        :param seed
        The seed to use for IPF.
        Must be a pd.Series with MultiIndex (origin zone, destination zone).
        """
        seed = seed.unstack()
        production = sparse_odm.groupby(level=0).sum().values
        attraction = sparse_odm.groupby(level=1).sum().values
        production += 0.0000001
        attraction += 0.0000001
        # ensure summation is the same between attraction and production
        attraction = attraction * (np.sum(production) / np.sum(attraction))

        values = ipf(seed.values, production, attraction, self.max_iter, self.tolerance)
        odm = pd.DataFrame(
            values,
            index=seed.index,
            columns=seed.columns
        ).stack()
        return odm


def ipf(seed, column_margin, row_margin, max_iter=5000, tolerance=1e-8):
    curr_seed = seed
    converged = False
    for i in range(max_iter):
        row_f = (row_margin / np.sum(curr_seed, axis=1))
        seed = (seed.T * row_f).T
        col_f = (column_margin / np.sum(seed, axis=0))
        seed = seed * col_f
        diff = np.amax(np.absolute(np.subtract(seed, curr_seed)))
        curr_seed = seed
        # Only check convergence every 10th iteration
        if i % 10 == 0 and diff < tolerance:
            converged = True
            print("IPF converged after", i, "iterations")
            break
    if not converged:
        print("IPF did not converge with tolerance", tolerance, "after", max_iter, "iterations")
    return curr_seed
