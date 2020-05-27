from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd


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
        twitter=gpd.sjoin(alignment_regions, twitter, how="inner", op='intersects').groupby('ID').size(),
        census=gpd.sjoin(alignment_regions, census, how="inner", op='intersects').groupby('ID').sum().population,
    )
    # Some regions might not have recorded population
    a = a.fillna(0)
    a = a.assign(
        twitter_perc=a.twitter / a.twitter.sum(),
        census_perc=a.census / a.census.sum(),
    )
    a = a.assign(perc_of_census=a.twitter_perc / a.census_perc)
    return a


def align_populations_aus_sao(alignment_regions, twitter):
    a = alignment_regions.assign(
        twitter=gpd.sjoin(alignment_regions, twitter, how="inner", op='intersects').groupby('zone').size(),
    )
    # Some regions might not have recorded population
    a = a.fillna(0)
    a = a.assign(
        twitter_perc=a.twitter / a.twitter.sum(),
        census_perc=a.census_population / a.census_population.sum(),
    )
    a = a.assign(perc_of_census=a.twitter_perc / a.census_perc)
    return a


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
