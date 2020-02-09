import pandas as pd
import os
from glob import glob
import plotly.figure_factory as ff

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


def value_timeseries(type, df=None, ylabel=''):
    if df is None:
        df = read_data()

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
    return df


def value_gantt(type, df=None):
    if df is None:
        df = read_data()

    df = df[df.type == type].groupby("id").apply(_gantt_grouper).reset_index()
    del df["level_1"]

    df = df.sort_values(by=["start","name"])

    events=[]
    for ix, row in df.iterrows():
        events.append(dict(
            Task=row["name"],
            Start=row.start,
            Finish=row.end,
        ))

    fig = ff.create_gantt(events, group_tasks=True, index_col='Task')
    return fig

