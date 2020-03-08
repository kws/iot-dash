import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.figure_factory as ff

__DEFAULT_DAYS = 7

_DB_URL = os.getenv("IOT_DB_URL")


def get_data(type, days=None):
    if days is None:
        days = __DEFAULT_DAYS

    start = datetime.now() - timedelta(days=days)

    with sqlite3.connect(_DB_URL) as conn:
        df = pd.read_sql_query(
            "select date,id,name,type,value from log where date>=? and type=? order by date",
            conn, params=[start, type])

    return df


def value_timeseries(type, days=None, ylabel=''):
    events = get_data(type, days=days)

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


def value_gantt(type, days=None):
    df = get_data(type, days=days)

    df = df.groupby("id").apply(_gantt_grouper).reset_index()
    del df["level_1"]

    df = df.sort_values(by=["Start","Task"])

    fig = ff.create_gantt(df, group_tasks=True, index_col='Task')
    fig.layout.xaxis.range = (datetime.now() - timedelta(days=days), datetime.now())
    return fig

