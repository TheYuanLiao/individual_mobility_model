import pandas as pd


def from_dfs(df):
    """
    :type df: pandas.DataFrame
    """
    df.sort_values(by='createdat')
    return 7
