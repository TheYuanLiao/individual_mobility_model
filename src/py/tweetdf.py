import pandas as pd


def tweet_df():
    df = pd.DataFrame([
        ["1", "12", "2006-11-06 14:37:20+00:00", "54.321", "12.345", "2", "1", "23"]
    ], columns=["userid", "tweetid", "createdat", "latitude", "longitude", "month", "weekday", "hourofday"])
    df["createdat"] = pd.to_datetime(df.createdat)
    return df


def from_csv(csvpath):
    df = pd.read_csv(csvpath)
    df["createdat"] = pd.to_datetime(df.createdat)
    df = df.sort_values(by='createdat')
    df = df.dropna()
    return df
