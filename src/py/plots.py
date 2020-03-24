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
    fig, ax = plt.subplots(1, 1, figsize=(20, 5))
    score.plot(
        ax=ax,
        kind='bar',
        rot=90,
        fontsize=10,
    )
    for n, lbl in enumerate(ax.xaxis.get_ticklabels()):
        if n % 5 != 0:
            lbl.set_visible(False)

    return fig
