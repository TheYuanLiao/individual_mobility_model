import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json

results_dir = '../results'


def string_range(strings, start=None, end=None):
    keep = []
    include = False
    for string in strings:
        if string.startswith('baseline'):
            keep.append(string)
        if string.startswith(start):
            include = True
        if include:
            keep.append(string)
        if end is not None and string.startswith(end):
            include = False
    return keep


def read_results(start=None, end=None, directories=None):
    if directories is None:
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
            #legend=False,
            xticks=[],
        )
        (data.sampers_weight - data.twitter_weight).unstack().plot(
            ax=axes[i, 1],
            rot=90,
            title="Delta Weight [{}]".format(title),
            #legend=False,
            xticks=[],
        )
    return fig


def plot_score_summary(national, east, west):
    def summary(df):
        return pd.DataFrame(
            [[
                (df.score * df.twitter_weight).sum(),
                (df.score * df.sampers_weight).sum(),
            ]],
            columns=['twitter_weighted', 'sampers_weighted']
        )

    fig, axes = plt.subplots(3, 1, figsize=(20, 10))
    for (title, data, ax) in zip(
            ['National', 'East', 'West'],
            [national, east, west],
            axes
    ):
        data.groupby('run_id').apply(summary).reset_index(level=1, drop=True).plot(kind='bar', ax=ax).legend(
            bbox_to_anchor=(1, 1))

    return fig



def read_distance_metrics(start=None, end=None, directories=None):
    if directories is None:
        result_directories = sorted(os.listdir(results_dir))
        directories = string_range(result_directories, start, end)

    return pd.concat([
        read_scale_distance_metrics(directories, "national"),
        read_scale_distance_metrics(directories, "east"),
        read_scale_distance_metrics(directories, "west"),
    ])


def read_scale_distance_metrics(directories, scale):
    metrics = None
    for d in directories:
        p = "{}/{}/distance-metrics-{}.csv".format(results_dir, d, scale)
        if not os.path.exists(p):
            continue
        s = pd.read_csv(p)
        s = s.assign(run_id=d, scale=scale).set_index(['scale', 'run_id', 'distance'])
        if metrics is None:
            metrics = s
        else:
            metrics = pd.concat([metrics, s])
    return metrics


def plot_distance_metrics(dms):
    fig, all_axes = plt.subplots(3, 2, figsize=(20,15), sharey=True)
    for (scale, axes) in zip(
        dms.index.get_level_values(level=0).unique(),
        all_axes
    ):
        for (col, ax) in zip(['model_mean', 'gravity_mean'], axes):
            ax.set_title("{} - {}".format(scale, col))
            dms.loc[scale][col].unstack(level=0).plot(
                ax=ax,
                rot=90,
                logy=True,
                xticks=[],
            ).legend(bbox_to_anchor=(1, 1))
            dms.loc[scale]['sampers_mean'].loc['baseline'].plot(
                ax=ax,
                rot=90,
                logy=True,
                xticks=[],
                label='sampers_mean'
            ).legend(bbox_to_anchor=(1, 1))
    return fig

def results_mse(directories=None, start=None, end=None, include_model=False):
    if directories is None:
        result_directories = sorted(os.listdir(results_dir))
        directories = string_range(result_directories, start, end)
        if include_model == True:
            directories.append('model')
    df = pd.DataFrame(columns=['scale', 'directory', 'p', 'gamma', 'beta', 'mse'])
    dms = read_distance_metrics(directories=directories)
    dms = dms[dms['sampers_mean'] != 0.0]
    df = mse(dms.loc['national'], 'national', df)
    df = mse(dms.loc['east'], 'east', df)
    df = mse(dms.loc['west'], 'west', df)
    return df

def mse(dms, scale, df):
    sq_errs = np.square(np.subtract(dms['sampers_sum'], dms['model_sum']))
    for model in dms.index.get_level_values(level=0).unique():
        with open(results_dir + '/' + model+ '/parameters.json') as f:
            d = json.load(f)

        if model != 'baseline':
            df2 = pd.DataFrame({'scale': [scale], 'directory': [model], 'p': [d['visits']['model']['p']], 'gamma': [d['visits']['model']['gamma']], 'beta': [d['visits']['model']['region_sampling']['beta']], 'mse': [sq_errs.loc[model].mean()]})
        else:
            df2 = pd.DataFrame({'scale': [scale], 'directory': [model], 'p': [None], 'gamma': [None], 'beta': [None], 'mse': [sq_errs.loc[model].mean()]})
        df = df.append(df2)
    return df


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
