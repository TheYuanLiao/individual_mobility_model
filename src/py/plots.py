import matplotlib as mpl
import matplotlib.pyplot as plt


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
    views = ['mean', 'variance']
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
