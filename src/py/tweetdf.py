import pandas


def tweet_df():
    df = pandas.DataFrame([
        ["1", "12", "2006-11-06 14:37:20+00:00", "54.321", "12.345", "2", "1", "23"]
    ], columns=["userid", "tweetid", "createdat", "latitude", "longitude", "month", "weekday", "hourofday"])
    df["createdat"] = pandas.to_datetime(df.createdat)
    return df
