import os
import sys
import matplotlib.pyplot as plt
import pandas as pd

results_dir = './../../results'


def string_range(strings, start=None, end=None):
    keep = []
    include = False
    for string in strings:
        if string.startswith(start):
            include = True
        if include:
            keep.append(string)
        if end is not None and string.startswith(end):
            include = False
    return keep


def read_results(start=None, end=None):
    result_directories = sorted(os.listdir(results_dir))
    directories = string_range(result_directories, start, end)
    scores_national = get_scale_results(directories, "national")
    scores_east = get_scale_results(directories, "east")
    scores_west = get_scale_results(directories, "west")

    return scores_national, scores_east, scores_west


def get_scale_results(directories, scale):
    scores = None
    for d in directories:
        s = pd.read_csv("{}/{}/score-{}.csv".format(results_dir, d, scale))
        s = s.assign(run_id=d).set_index(['quantile', 'run_id'])
        if scores is None:
            scores = s
        else:
            scores = pd.concat([scores, s])
    return scores


def plot_scores(snational, seast, swest):
    fig, axes = plt.subplots(3, 2, figsize=(20, 10))
    for (title, data, i) in zip(
            ["National", "East", "West"],
            [snational, seast, swest],
            range(3),
    ):
        data.score.unstack().plot(
            ax=axes[i, 0],
            rot=90,
            title="Score [{}]".format(title),
            legend=False,
            xticks=[],
        )
        (data.sampers_weight - data.twitter_weight).unstack().plot(
            ax=axes[i, 1],
            rot=90,
            title="Delta Weight [{}]".format(title),
            legend=False,
            xticks=[],
        )
    return fig


if __name__ == "__main__":
    print(len(sys.argv))
    if len(sys.argv) < 2 or 3 < len(sys.argv):
        print("invalid arguments")
        print("resultcomp.py start [end]")

    start = sys.argv[1]
    end = sys.argv[2] if len(sys.argv) > 2 else None

    results = read_results(start, end)
    snational, seast, swest = read_results(start=start, end=end)
    _ = plot_scores(snational, seast, swest)
    plt.tight_layout()
    plt.show()
