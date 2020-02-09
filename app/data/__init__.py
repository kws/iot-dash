import pandas as pd
import os
from glob import glob
import plotly.figure_factory as ff
from datetime import datetime, timedelta

__DEFAULT_DAYS = 7

_DIR = os.getenv("IOT_DIR", os.path.abspath("../samples"))
_columns = [
    "date",
    "id",
    "name",
    "type",
    "value",
    "battery",
    "dark",
    "daylight"
]


def read_data():
    files = glob(os.path.join(_DIR, "iot-log-*.csv*"))
    dataframes = [pd.read_csv(f, names=_columns, parse_dates=["date"]) for f in files]
    df = pd.concat(dataframes)
    df = df.drop_duplicates()
    df = df.sort_values("date")
    return df


def get_data(df=None, days=None):
    if df is None:
        df = read_data()

    if days is None:
        days = __DEFAULT_DAYS

    df = df[df.date >= datetime.now() - timedelta(days=days)]
    return df


def value_timeseries(type, df=None, days=None, ylabel=''):
    df = get_data(df=df, days=days)

    events = df[df.type == type]
    traces=[]

    for name in sorted(events.name.unique()):
        series = events[events.name == name]
        traces.append(dict(
            x=series.date,
            y=series.value,
            text=series.value,
            mode='line',
            opacity=0.7,
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=name
        ))

    return {
        'data': traces,
        'layout': dict(
            xaxis={'title': 'Date'},
            yaxis={'title': ylabel},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            transition={'duration': 500},
        )
    }


def _gantt_grouper(df):
    df = df.sort_values("date").reset_index()
    df.loc[df.value == 'true', 'start'] = df.date
    df.loc[df.value == 'false', 'end'] = df.date
    df.fillna(method='bfill', inplace=True)
    df = df[df.start < df.end]
    df = df[["name", "start", "end"]].drop_duplicates()
    df.columns =  ["Task","Start",'Finish']
    return df


def value_gantt(type, days=None, df=None):
    df = get_data(df=df, days=days)

    df = df[df.type == type].groupby("id").apply(_gantt_grouper).reset_index()
    del df["level_1"]

    df = df.sort_values(by=["Start","Task"])

    fig = ff.create_gantt(df, group_tasks=True, index_col='Task')
    fig.layout.xaxis.range = (datetime.now() - timedelta(days=days), datetime.now())
    return fig

