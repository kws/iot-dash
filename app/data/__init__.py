import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.figure_factory as ff

__DEFAULT_DAYS = 1

_DB_URL = os.getenv("IOT_DB_URL")


def get_data(type, days=None):
    if days is None:
        days = __DEFAULT_DAYS

    start = datetime.utcnow() - timedelta(days=days)
    start = start.strftime('%Y-%m-%dT%H:%M:%S')

    with sqlite3.connect(_DB_URL) as conn:
        df = pd.read_sql_query(
            "select l.date,l.id,s.name,l.type,l.value,s.sort_order from log as l"
            "  left join sensors as s on l.id = s.id "
            "  where l.date>=? and l.type=? order by l.date",
            conn, params=[start, type])

    return df


def value_timeseries(type, days=None, ylabel=''):
    events = get_data(type, days=days)

    traces=[]

    for name in sorted(events.sort_order.unique()):
        series = events[events.sort_order == name]
        display_name = series.name.values[0]
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
            name=display_name
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
    df.loc[df.value == '1', 'start'] = df.date
    df.loc[df.value == '0', 'end'] = df.date
    df.fillna(method='bfill', inplace=True)
    df = df[df.start < df.end]
    df = df[["name", "start", "end", "sort_order"]].drop_duplicates()
    df.columns =  ["Task","Start","Finish","Sort"]
    return df


def value_gantt(type, days=None):
    df = get_data(type, days=days)

    df = df.groupby("id").apply(_gantt_grouper).reset_index()
    del df["level_1"]

    df = df.sort_values(by=["Sort", "Start","Task"])

    if df.shape[0] == 0:
        return {}

    fig = ff.create_gantt(df, group_tasks=True, index_col='Task')
    fig.layout.xaxis.range = (datetime.now() - timedelta(days=days), datetime.now())
    return fig

