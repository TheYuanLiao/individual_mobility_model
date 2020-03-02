# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:48:00 2020

@author: Yuan Liao
This is the script to generate OD using a simple gravity model and compare the model output
with sampers' output.

Data source: Twitter user timelines, sampers' outputs
Method: Gravity model
Calibration method: against itself.
Similarity measure: SpSSIM
Time: an average weekday
Scale: nation, goteborg, stockholm

"""

import pandas as pd
import geopandas as gpd
import numpy as np
import math
from ipfn import ipfn


def od_df_to_od_matrix(df, zone_to_index, trips_var):
    """
    input:
        df - ["ozone", "dzone", var1, var2, ...],
        zone_to_index - {"zone" : zone_index_in_matrix},
        orig_var - origin column in df,
        dest_var - destination column in df,
        trips_var - number of trips / probability of trips using different data sources
    output:
        matrix_odm - OD matrix in numpy matrix format with cell value of trips_var

    """
    zones_num = len(zone_to_index)
    matrix_odm = np.zeros((zones_num, zones_num))
    df = df[df[trips_var] != 0]
    for _, row in df.iterrows():
        origin = zone_to_index[row['ozone']]
        destination = zone_to_index[row['dzone']]
        matrix_odm[origin, destination] = row[trips_var]
    return matrix_odm


def costMatrixGenerator_np(d_OD, beta):
    """
    input:
        d_OD - the OD matrix with the distance as the cell value; distance is the Haversine distance between traffice zones' centroids,
        beta - parameter of the gravity model
    output:
        myfunc_vec(d_OD) - OD matrix with the cost of travelling between OD pairs as the cell value

    """
    myfunc_vec = np.vectorize(lambda x: math.exp(-beta * x))
    return myfunc_vec(d_OD)


def tripDistribution_np(tripGeneration, costMatrix, production_field, attraction_field):
    """
    input:
        tripGeneration - the dataframe with production and attraction ready,
        costMatrix - output from costMatrixGenerator_np(d_OD, beta),
        production_field - e.g., lg_prod_a for Twitter data,
        attraction_field - e.g., lg_attr_a for Twitter data

    output:
        trips - OD matrix as the model output in dataframe format

    """
    production = tripGeneration[production_field].values
    attraction = tripGeneration[attraction_field].values
    aggregates = [production, attraction]
    dimensions = [[0], [1], [0, 1]]
    IPF = ipfn.ipfn(costMatrix, aggregates, dimensions, max_iteration=5000)
    trips = IPF.iteration()
    trips = pd.DataFrame(trips, index=tripGeneration.zone, columns=tripGeneration.zone)
    return trips


def shape_to_zone_dictionary(shape):
    shp = shape.reset_index(drop=False).set_index('zone')
    return shp.to_dict()['index']


def gravity_model(df_shp, df_tw, beta):
    """
    input:
        df_shp - shape df, one option in ["nation", "goteborg", "stockholm"],
        beta - the parameter of gravity model (you can use 0.03),
        df_tw - the empirical od pair from Twitter
    output:
        df_OD - OD matrix as the model output in dataframe format (normalised),
        W - the OD matrix with the distance as the cell value; distance is the Haversine distance between traffice zones' centroids,
        re_index_dict - {"zone" : zone_index_in_matrix},
        zones_num - the number of traffic zones
    """
    ### Production and attraction
    sampling = "count"
    df_tw_prod = df_tw.groupby("ozone")[sampling].sum().reset_index()
    df_tw_prod.rename(columns={"ozone": "zone", sampling: sampling + "_prod_a"}, inplace=True)
    df = df_shp.merge(df_tw_prod, on=["zone"], how="outer")

    df_tw_attr = df_tw.groupby("dzone")[sampling].sum().reset_index()
    df_tw_attr.rename(columns={"dzone": "zone", sampling: sampling + "_attr_a"}, inplace=True)
    df = df.merge(df_tw_attr, on=["zone"], how="outer")

    ### Production and attraction process to balance
    df["count_attr_a"] = df["count_prod_a"].sum() * df["count_attr_a"] / df["count_attr_a"].sum()
    ## Define distance matrix -> Cost matrix
    s = df_shp.copy()
    s['key'] = 1
    zone_distances = pd.merge(s, s, how="outer", on='key')
    zone_distances['d'] = zone_distances.apply(lambda row: (row['geometry_x'].centroid.distance(row['geometry_y'].centroid) / 1000), axis=1)
    zone_distances = zone_distances.rename(columns={'zone_x': 'ozone', 'zone_y': 'dzone'})[['ozone', 'dzone', 'd']]
    zone_distances["ozone"] = zone_distances["ozone"].astype(int)
    zone_distances["dzone"] = zone_distances["dzone"].astype(int)
    zone_to_index = shape_to_zone_dictionary(df_shp)
    W = od_df_to_od_matrix(zone_distances, zone_to_index, 'd')

    ## Model OD construction
    production_field = "count_prod_a"
    attraction_field = "count_attr_a"
    df = df.fillna(value={production_field: 0, attraction_field: 0})
    costMatrix = costMatrixGenerator_np(W, beta)
    trips = tripDistribution_np(df, costMatrix, production_field, attraction_field)
    matrix_sim = trips.values
    matrix_sim = matrix_sim / matrix_sim.sum()  # Normalise into 0-1

    ## Model OD to od pair dataframe and merge back to the ground truth od data
    zones_num = len(zone_to_index)
    zone_to_index_rev = {v: k for k, v in zone_to_index.items()}
    OD_list = []
    for i in range(0, zones_num):
        for j in range(0, zones_num):
            OD_list.append((zone_to_index_rev[i], zone_to_index_rev[j], matrix_sim[i, j]))
    df_OD = pd.DataFrame(OD_list, columns=["ozone", "dzone", sampling])
    df_OD = df_OD.fillna(0)
    df_OD["ozone"] = df_OD["ozone"].astype(int)
    df_OD["dzone"] = df_OD["dzone"].astype(int)
    return zone_distances, zone_to_index, W, df_OD


def OD2simi(OD_baseline, OD, W, bins, hist, C1, C2):
    """
    input:
        OD_baseline - "ground-truth" OD,
        OD - Twitter OD,
        W - the OD matrix with the distance as the cell value; distance is the Haversine distance between traffice zones' centroids,
        bins - [(d1, d2)] a series of distance ranges/groups
        hist - the number of OD pairs in each distance bin
        C1, C2 - constants (10**(-16), 10**(-10))
    output:
        SpSSIM_mean - Similarity value,
        SpSSIM_share_mean - Similarity value weighted by travel demand to avoid artefact of high similarity values,
        df_comp - Similarity value by distance range, columns = ['d_range', 'freq', 'share', 'SpSSIM']
    """
    SpSSIM = []
    SpSSIM_mean = 0
    SpSSIM_share_mean = 0
    bin_count = 0
    for d_bin in bins:
        freq = hist[bin_count]
        if freq != 0:
            scale = lambda x: 1 if (x >= d_bin[0]) & (x < d_bin[1]) else 0
            vfunc = np.vectorize(scale)
            W_test = vfunc(W)
            Wx = OD_baseline * W_test
            Wy = OD * W_test
            Wx = np.array(Wx).flatten()
            Wy = np.array(Wy).flatten()
            trip_weight = Wx.sum()
            SpSSIM_ele = (2 * Wx.mean() * Wy.mean() + C1) * (2 * np.cov(Wx, Wy)[0][1] + C2) / (
                    (Wx.mean() ** 2 + Wy.mean() ** 2 + C1) * (Wx.var() + Wy.var() + C2))
            SpSSIM.append((d_bin[0], d_bin[1], freq, trip_weight, SpSSIM_ele))
            SpSSIM_mean += SpSSIM_ele
            SpSSIM_share_mean += SpSSIM_ele * trip_weight
            bin_count += 1
    SpSSIM_mean = SpSSIM_mean / bin_count  # valid_count, bin_count
    df_comp = pd.DataFrame()
    df_comp["d_range"] = [(x[0], x[1]) for x in SpSSIM]
    df_comp["freq"] = [x[2] for x in SpSSIM]
    df_comp["share"] = [x[3] for x in SpSSIM]
    df_comp["SpSSIM"] = [x[4] for x in SpSSIM]
    return SpSSIM_mean, SpSSIM_share_mean, df_comp


def similarity(df_gt, df_tw, shape, scale):
    beta = 0.03
    zone_distances, zone_to_index, W, df_OD = gravity_model(shape, df_tw, beta)
    OD_tw = od_df_to_od_matrix(df_OD, zone_to_index, "count")
    df_gt["ozone"] = df_gt["ozone"].astype(int)
    df_gt["dzone"] = df_gt["dzone"].astype(int)
    OD_gt = od_df_to_od_matrix(df_gt, zone_to_index, "total")

    # Focus on the OD pairs that have distance longer than 100 km
    distance_filter = W < 100
    zone_distances = zone_distances.set_index(['ozone', 'dzone'])
    df_tw.apply(lambda row: zone_distances.loc[(row['ozone'], row['dzone']), 'd'], axis=1)
    df_tw['d'] = df_tw.apply(lambda row: zone_distances.loc[(row['ozone'], row['dzone']), 'd'], axis=1)
    # Create bins for similarity calculation
    if scale == "national":
        df_tw = df_tw[df_tw["d"] >= 100]
        bins_scale = [100] + [df_tw["d"].quantile(x / 100) for x in range(1, 101, 1)]
    else:
        bins_scale = [0] + [df_tw["d"].quantile(x / 100) for x in range(1, 101, 1)]
    hist, bin_edges = np.histogram(df_tw["d"], bins=bins_scale)  # "fd", bins_dict[scale]
    bins = [(x, y) for x, y in zip(bin_edges[:-1], bin_edges[1:])]

    # Implement the distance filter for national scale
    if scale == "national":
        OD_gt[distance_filter] = 0
        OD_tw[distance_filter] = 0

    # Normalise OD to 0-1
    OD_gt = OD_gt / OD_gt.sum()
    OD_tw = OD_tw / max(OD_tw.sum(), 1)

    # Define the constants value for SpSSIM
    C1, C2 = 10 ** (-16), 10 ** (-10)
    SpSSIM_mean, SpSSIM_share_mean, df_comp = OD2simi(OD_gt, OD_tw, W, bins, hist, C1, C2)

    # Print out the results
    print("Similarity:", SpSSIM_mean, "Similarity weighted by travel demand:", SpSSIM_share_mean)
    print("Similarity by distance group:\n", df_comp)
    return SpSSIM_mean, SpSSIM_share_mean, df_comp, OD_gt, OD_tw
