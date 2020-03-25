import matplotlib as mpl
import matplotlib.pyplot as plt


def plot_odms(sparse_odm, dense_odm, sampers_odm):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=True, sharey=True)
    fig.set_size_inches(18.5, 10.5)
    ax1.set_title('Sparse ODM')
    ax1.imshow(sparse_odm.unstack().values, norm=mpl.colors.LogNorm())
    ax2.set_title('ODM')
    ax2.imshow(dense_odm.unstack().values, norm=mpl.colors.LogNorm())
    ax3.set_title('Sampers')
    ax3.imshow(sampers_odm.unstack().values, norm=mpl.colors.LogNorm())

    return fig


def plot_spssim_score(score):
    subplot_line_config = {
        # Hide xticks for subplots
        'xticks': [],
    }
    fig = plt.figure(figsize=(20, 12), constrained_layout=True)
    gs = fig.add_gridspec(2, 3)
    plots = [
        (
            "Score",
            fig.add_subplot(gs[0, :]),
            score[['score']],
        ),
        (
            "Weight",
            fig.add_subplot(gs[1, 0]),
            score[['sampers_weight', 'twitter_weight']],
            subplot_line_config,
        ),
        (
            "Variance",
            fig.add_subplot(gs[1, 1]),
            score[['sampers_var', 'twitter_var']],
            subplot_line_config,
        ),
        (
            "Covariance",
            fig.add_subplot(gs[1, 2]),
            score[['covariance']],
            subplot_line_config,
        ),
    ]
    for p in plots:
        title = p[0]
        ax = p[1]
        data = p[2]
        line_overrides = p[3] if len(p) == 4 else {}
        ax.set_title(title, fontsize=20, fontweight='bold')
        data.plot(
            ax=ax,
            kind='line',
            rot=90,
            fontsize=18,
            **line_overrides,
        )
    return fig
