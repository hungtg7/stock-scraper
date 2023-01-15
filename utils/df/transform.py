import pandas
from datetime import date


def sor_by_col(df, col: str, asc: bool = False):
    return df.sort_values(by=col, ascending=asc)


def upsert(df1, df2):
    if df1 is None:
        return df2

    df = pandas.concat([df1, df2[~df2.index.isin(df1.index)]])
    df.update(df2)
    return df


def transform_t_col(df, col):
    today = date.today()
    YYMMDD_today = today.strftime("%Y-%m-%d")
    df1 = pandas.to_datetime(
            YYMMDD_today + " " + df[col], format="%Y-%m-%d %H%M%S") + pandas.DateOffset(hours=7)
    df[col] = df1
    return df
