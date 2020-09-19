import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.metrics import pairwise_distances
import lib.sampers as sampers
import lib.mscthesis as mscthesis

scales = ['national', 'east', 'west']


class Sampers:
    def __init__(self):
        self.zones = dict()
        self.distances = dict()
        self.odm = dict()
        self.quantile_groups = dict()

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

            print("Calculating quantiles...")
            quantiles = pd.qcut(distances, q=100)
            qgrps = quantiles.groupby(quantiles)

            self.zones[scale] = zones
            self.distances[scale] = distances
            self.odm[scale] = odm
            self.quantile_groups[scale] = qgrps
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
        if point_visits.shape[0] > 0:
            n_point_visits_before = point_visits.shape[0]
            point_visits = gpd.sjoin(point_visits, self.zones[scale], op='intersects')
            print("removed", n_point_visits_before - point_visits.shape[0], "point-visits due to missing zone geom")
        else:
            point_visits = point_visits.assign(zone='0')

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

        sparse_odm = mscthesis.visit_gaps(visits[['zone']]) \
            .groupby(['zone_origin', 'zone_destination']).size() \
            .reindex(self.odm[scale].index, fill_value=0.0)

        sparse_odm = sparse_odm / sparse_odm.sum()
        return sparse_odm

    def distance_cut(self, scale, odm):
        if scale == 'national':
            odm[self.distances[scale] < 100] = 0

        return odm / odm.sum()


class DistanceMetrics:
    def __init__(self):
        pass

    def compute(self, quantile_groups=None, odms=None, titles=None):
        """
        :param quantile_groups:
        pd.SeriesGroupby mapping distance groups to indexes.
        Obtained by Sampers.prepare
        """
        if len(odms) != len(titles):
            raise Exception("odms and titles must have same length")
        metrics = []
        for grpkey in quantile_groups.groups:
            odm_grps = [o.iloc[quantile_groups.indices[grpkey]] for o in odms]
            metrics.append(
                [grpkey] + [g.sum() for g in odm_grps]
            )
        return pd.DataFrame(
            metrics,
            columns=['distance'] + [t + '_sum' for t in titles]
        ).set_index('distance')

    def kullback_leibler(self, distances, titles=None):
        """
        :param distances:
        A data frame, output of compute(); _sum will be used to calculate Kullback-Leibler divergence measure
        titles[0] ground truth, titles[1] model
        """
        if (titles is None) | (len(titles) != 2):
            raise Exception("Two distance distributions need to be specified.")

        dis = distances.loc[(distances[titles[0] + '_sum'] != 0) | (distances[titles[1] + '_sum'] != 0), :]
        L = len(dis)
        d_ground_truth = dis[titles[0] + '_sum'].values
        d_model = dis[titles[1] + '_sum'].values
        # find zeros to merge to the next bin freq rate
        zeros = list(np.where(d_ground_truth == 0)[0]) + list(np.where(d_model == 0)[0])
        zeros = list(set(zeros))
        tomerge = list(set(zeros + [x + 1 for x in zeros if x < L - 1] + [x - 1 for x in zeros if x == L - 1]))
        tomerge = sorted(tomerge)
        if not tomerge:
            d_gt_out = d_ground_truth
            d_m_out = d_model
        else:
            d_gt_out = d_ground_truth[0:tomerge[0]]
            d_m_out = d_model[0:tomerge[0]]
            end_ind = tomerge[0]
            start_ind = end_ind
            i = 0
            while i < len(tomerge):
                if end_ind < tomerge[i]:
                    end_ind = tomerge[i]
                    d_gt_out = np.append(d_gt_out, d_ground_truth[start_ind:end_ind])
                    d_m_out = np.append(d_m_out, d_model[start_ind:end_ind])
                    start_ind = end_ind
                else:
                    if (i == len(tomerge) - 1) | (tomerge[min(len(tomerge) - 1, i + 1)] - tomerge[i] > 1):
                        end_ind = tomerge[i] + 1
                        d_gt_out = np.append(d_gt_out, [sum(d_ground_truth[start_ind:end_ind])])
                        d_m_out = np.append(d_m_out, [sum(d_model[start_ind:end_ind])])
                        start_ind = end_ind
                    else:
                        end_ind = tomerge[i + 1]
                    i = i + 1
        if len(np.where(d_m_out == 0)[0]) == 0:
            d_kl = sum(d_gt_out * np.log10(d_gt_out / d_m_out))
        else:
            d_kl = 999
        return d_kl