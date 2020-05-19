import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def plot_odms(odms=None, titles=None):
    if len(odms) != len(titles):
        raise Exception("Odms and titles must have same length")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(odms),
        figsize=(20, 10),
        sharex=True,
        sharey=True,
    )
    if len(odms) == 1:
        axes = [axes]

    for (odm, title, ax) in zip(odms, titles, axes):
        ax.set_title(title)
        ax.imshow(
            odm.unstack().values,
            norm=mpl.colors.LogNorm(),
        )

    return fig


def plot_spssim_score(score):
    fig, [ax1, ax2] = plt.subplots(1, 2, figsize=(20, 5), constrained_layout=True)
    ax1.set_title("Score")
    score[['score']].plot(
        ax=ax1,
        kind='line',
        rot=90,
    )
    score[['sampers_weight', 'twitter_weight']].plot(
        ax=ax2,
        style='--',
        rot=90,
    )
    return fig


def plot_distance_metrics(distance_metrics, prefixes=None, show_norm=True, show_log=True):
    if prefixes is None:
        raise Exception("prefixes must be set")
    views = ['sum', 'mean', 'variance']
    fig, axes = plt.subplots(len(views), 1, figsize=(15, 4 * len(views)))
    for (view, ax) in zip(views, axes):
        ax.set_title(view.capitalize())
        columns = [p + '_' + view for p in prefixes]
        if show_norm:
            distance_metrics[columns].plot(
                ax=ax,
            ).legend(
                labels=prefixes,
                # put legend outside of plot for visibility
                loc='upper left',
                bbox_to_anchor=(1.05, 1)
            )
        if show_log:
            logax = ax.twinx()
            distance_metrics[columns].plot(
                ax=logax,
                logy=True,
                style='--',
            ).legend(
                labels=[p + ' (log10)' for p in prefixes],
                # put legend outside of plot for visibility
                loc='upper left',
                bbox_to_anchor=(1.05, 0.65)
            )
    return fig

def plot_visitation_frequency(tweets, ax, title='Baseline'):
    n_largest_locs = tweets.groupby(['userid', 'region']).size()
    n_largest_locs_20 = n_largest_locs.groupby('userid').nlargest(20).droplevel(1)
    n_largest_locs_40 = n_largest_locs.groupby('userid').nlargest(40).droplevel(1)
    n_largest_locs_60 = n_largest_locs.groupby('userid').nlargest(60).droplevel(1)
    n_largest_locs_20x = n_largest_locs_20.to_frame().groupby('userid').apply(lambda df: df.assign(rank=np.add(np.arange(len(df)), 1)))
    n_largest_locs_40x = n_largest_locs_40.to_frame().groupby('userid').apply(lambda df: df.assign(rank=np.add(np.arange(len(df)), 1)))
    n_largest_locs_60x = n_largest_locs_60.to_frame().groupby('userid').apply(lambda df: df.assign(rank=np.add(np.arange(len(df)), 1)))
    n_largest_locs_20y = n_largest_locs_20x.groupby('rank').sum()[0]
    n_largest_locs_20y = n_largest_locs_20y / (n_largest_locs_20x.reset_index()[['userid', 'rank']].groupby('rank').count()['userid'])
    n_largest_locs_40y = n_largest_locs_40x.groupby('rank').sum()[0]
    n_largest_locs_40y = n_largest_locs_40y / (n_largest_locs_40x.reset_index()[['userid', 'rank']].groupby('rank').count()['userid'])
    n_largest_locs_60y = n_largest_locs_60x.groupby('rank').sum()[0]
    n_largest_locs_60y = n_largest_locs_60y / (n_largest_locs_60x.reset_index()[['userid', 'rank']].groupby('rank').count()['userid'])

    mpl.rcParams['font.size'] = 20.0
    values_20, base_20 = np.histogram(n_largest_locs_20y.index, weights=n_largest_locs_20y.values, bins=np.add(np.arange(21), 1), density=True)
    values_40, base_40 = np.histogram(n_largest_locs_40y.index, weights=n_largest_locs_40y.values, bins=np.add(np.arange(41), 1), density=True)
    values_60, base_60 = np.histogram(n_largest_locs_60y.index, weights=n_largest_locs_60y.values, bins=np.add(np.arange(61), 1), density=True)
    ax.plot(base_20[:-1], values_20, 'v', c='blue', markersize=5, label='S = 20', zorder=3)
    ax.plot(base_40[:-1], values_40, 'o', c='red', markersize=5, label='S = 40', zorder=2)
    ax.plot(base_60[:-1], values_60, 's', c='black', markersize=5, label='S = 60', zorder=1)
    ax.set_ylabel('$f_k$')
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlabel('k')
    ax.legend(loc='best', frameon=False)
    ax.set_ylim(0.001, 1)
    ax.set_xlim(0.9, 100)
    ax.set_title(title)
    return ax


def plot_distinct_locs_over_time(tweets, label='Emperical'):
    new_locs_by_user_date = tweets.groupby(['userid', 'region']).apply(lambda x: x['date'].sort_values().head(1))
    new_locs_by_user_date = new_locs_by_user_date.droplevel(2).reset_index(1)
    new_locs_by_user_date = new_locs_by_user_date.groupby(['userid', 'date']).size()
    new_locs_by_user_date = new_locs_by_user_date.to_frame().groupby('userid').apply(lambda df: df.assign(consecutive_day=np.arange(len(df))))
    new_locs_by_date = new_locs_by_user_date.reset_index().groupby('consecutive_day').sum()[0]
    users_per_date = new_locs_by_user_date.reset_index().groupby('consecutive_day')['userid'].size()
    avg_new_locs_by_date = new_locs_by_date / users_per_date

    mpl.rcParams['font.size'] = 20.0
    values, base = np.histogram(avg_new_locs_by_date.index, weights=avg_new_locs_by_date.values, bins=528)
    cumulative = np.cumsum(values)
    fig = plt.figure(figsize=(7, 10))
    plt.plot(base[:-1], cumulative, 'o', c='blue', markersize=4, label=label)
    plt.ylabel('S(t)')
    plt.xlabel('t (days)')
    plt.yscale('log')
    plt.xscale('log')
    plt.ylim(0.9, 1000)
    plt.xlim(0.9, 1000)
    x = np.linspace(0, 1000, 1000)
    plt.plot(x, x, ls="--", c=".3", label='~t');
    plt.legend(loc='best', frameon=False)
    return fig


def plot_dist_distribution(dms, scale):
    mpl.rcParams['font.size'] = 20.0
    fig, axes = plt.subplots(2, 1, figsize=(20, 13), sharex=True)
    axes[0].set_title(scale.title())
    dms.loc[scale]['model_sum'].unstack(level=0).cumsum().plot(
        ax=axes[0],
        rot=90,
        xticks=[],
    )
    dms.loc[scale]['sampers_sum'].loc['Baseline'].cumsum().plot(
        ax=axes[0],
        rot=90,
        xticks=[],
        label='Sampers'
    )
    axes[0].set_xlabel('Distance')
    axes[0].set_ylabel('Cumulative percentage of trips')
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].get_legend().remove()

    n = dms.loc[scale]
    sq_err = np.square(np.subtract(n['sampers_sum'], n['model_sum']))
    print('Baseline MSE: {:.5e}'.format(sq_err.loc['Baseline'].mean()))
    print('Model MSE: {:.5e}'.format(sq_err.loc['Model'].mean()))
    sq_err.unstack(level=0).cumsum().plot(
        ax=axes[1],
        rot=90,
        xticks=[],
    )
    axes[1].set_ylabel('Cumulative squared error')
    axes[1].set_xlabel('Distance')
    axes[1].get_legend().remove()
    axes[0].xaxis.set_tick_params(labelbottom=False)

    axes[0].text(-0.1, .8, "A", transform=axes[0].transAxes, fontsize='25')
    axes[1].text(-0.1, .8, "B", transform=axes[1].transAxes, fontsize='25')

    return fig, axes


def generic_plot_dist_distribution(ax, distance_sums=[], titles=[], ticks=None, yscale='log'):
    #ax.set_title("Trip distance distribution")

    for d in distance_sums:
        ax.plot(d.index.right, d.values, zorder=2)

    for x in distance_sums[0].index.left:
        ax.axvline(x, color='black', linewidth=0.25, zorder=1)
    ax.axvline(distance_sums[0].index.right[-1], color='black', linewidth=0.25, zorder=1)
    ax.set_xscale('log')
    ax.set_yscale(yscale)
    ax.set_ylabel('Percentage of trips')
    ax.set_xlabel('Distance (km)')
    ax.legend(labels=titles)
    if ticks is not None:
        ax.set_xticks(ticks)
        ax.get_xaxis().set_major_formatter(mpl.ticker.ScalarFormatter())

