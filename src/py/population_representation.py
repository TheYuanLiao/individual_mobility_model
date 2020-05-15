from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import geopandas as gpd
import numpy as np


def twitter_home_locations(region):
    twitter_homes = pd.read_csv("./../../dbs/" + region + "/homelocations.csv")
    return gpd.GeoDataFrame(
        twitter_homes,
        crs='EPSG:4326',
        geometry=gpd.points_from_xy(twitter_homes['longitude'], twitter_homes['latitude']),
    )


def plot_home_locations(census_zones, twitter_homes):
    fig, ax = plt.subplots(1, 1, figsize=(2, 2))
    census_zones.plot(ax=ax, facecolor='none', edgecolor='black')
    twitter_homes.plot(ax=ax, markersize=0.5)
    ax.tick_params(labelsize=4)


def align_populations(alignment_regions, twitter, census):
    a = alignment_regions.assign(
        twitter = gpd.sjoin(alignment_regions, twitter, how="inner", op='intersects').groupby('ID').size(),
        census = gpd.sjoin(alignment_regions, census, how="inner", op='intersects').groupby('ID').sum().population,
    )
    # Some regions might not have recorded population
    a = a.fillna(0)
    a = a.assign(
        twitter_perc = a.twitter / a.twitter.sum(),
        census_perc = a.census / a.census.sum(),
    )
    a = a.assign(perc_of_census = a.twitter_perc / a.census_perc)
    return a


def align_populations_aus_sao(alignment_regions, twitter):
    a = alignment_regions.assign(
        twitter = gpd.sjoin(alignment_regions, twitter, how="inner", op='intersects').groupby('zone').size(),
    )
    # Some regions might not have recorded population
    a = a.fillna(0)
    a = a.assign(
        twitter_perc = a.twitter / a.twitter.sum(),
        census_perc = a.census_population / a.census_population.sum(),
    )
    a = a.assign(perc_of_census = a.twitter_perc / a.census_perc)
    return a


def plot_geo_rep(counties, municipalities, ticks1=None, ticks2=None):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 10))
    ax1.set_axis_off()
    ax2.set_axis_off()
    plot_cfg = {
        "column": "perc_of_census",
        "legend": True,
        "edgecolor": "black",
        "linewidth": 0.1,
        "cmap": "bwr",
    }
    legend_kwds = {
        "orientation": "horizontal",
        "fraction": 0.5,
        "pad": 0.01,
        "shrink": 1.,
        "format": mpl.ticker.PercentFormatter(xmax=1.),
    }

    counties_limit = np.max(counties.perc_of_census)
    counties.plot(
        ax=ax1,
        norm=mpl.colors.DivergingNorm(vmin=0., vcenter=1., vmax=counties_limit),
        **plot_cfg,
        legend_kwds=dict(**legend_kwds, ticks=ticks1)
    )
    ax1.text(.05, .8, "A", transform=ax1.transAxes, fontsize='25')

    municipalities_limit = np.max(municipalities.perc_of_census)
    municipalities.plot(
        ax=ax2,
        norm=mpl.colors.DivergingNorm(vmin=0, vcenter=1., vmax=municipalities_limit),
        **plot_cfg,
        legend_kwds=dict(**legend_kwds, ticks=ticks2)
    )
    ax2.text(.05, .8, "B", transform=ax2.transAxes, fontsize='25')


def plot_geo_rep_aus_sao(study_zone):
    mpl.rcParams['font.size'] = 18.0

    fig, ax = plt.subplots(1, 1, figsize=(20, 13))
    ax.set_axis_off()
    plot_cfg = {
        "column": "perc_of_census",
        "legend": True,
        "edgecolor": "black",
        "linewidth": 0.1,
        "cmap": "bwr",
    }
    legend_kwds = {
        "orientation": "horizontal",
        "pad": 0.01,
        "shrink": 1.,
        "format": mpl.ticker.PercentFormatter(xmax=1.),
    }

    study_zone.plot(
        ax=ax,
        norm=mpl.colors.DivergingNorm(vmin=0., vcenter=1., vmax=np.max(study_zone.perc_of_census)),
        **plot_cfg,
        legend_kwds=dict(**legend_kwds)
    )


def plot_corr(counties, municipalities):
    fig, axes = plt.subplots(1, 2, figsize=(18, 8.5))

    scatter_style = {
        "kind": "line",
        "x": "census_perc",
        "y": "twitter_perc",
        "loglog": True,
        "marker": "o",
        "markersize": 3,
        "linestyle": "None",
        "legend": False,
    }
    pd.DataFrame(counties).plot(
        ax=axes[0],
        **scatter_style,
    )

    pd.DataFrame(municipalities).plot(
        ax=axes[1],
        **scatter_style,
    )
    for ax in axes:
        for axis in [ax.xaxis, ax.yaxis]:
            axis.set_major_formatter(ScalarFormatter())
        ax.plot([0, 0.5], [0, 0.5], color='black', linewidth=0.25)
        ax.set_xlabel('Census percentage of population', fontsize=20)
        ax.set_ylabel('Twitter percentage of population', fontsize=20)
    axes[0].grid(True)
    axes[1].grid(True)
    axes[0].text(.05, .9, "A", transform=axes[0].transAxes, fontsize='25')
    axes[1].text(.05, .9, "B", transform=axes[1].transAxes, fontsize='25')
    return axes

def plot_corr_aus_sao(study_zone):
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 8.5))

    scatter_style = {
        "kind": "line",
        "x": "census_perc",
        "y": "twitter_perc",
        "loglog": True,
        "marker": "o",
        "markersize": 3,
        "linestyle": "None",
        "legend": False,
    }
    pd.DataFrame(study_zone).plot(
        ax=ax,
        **scatter_style,
    )
    ax.plot([0, 0.5], [0, 0.5], color='black', linewidth=0.25)
    ax.set_xlabel('Census percentage of population', fontsize=20)
    ax.set_ylabel('Twitter percentage of population', fontsize=20)
    ax.grid(True)
    return ax

