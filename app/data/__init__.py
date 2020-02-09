import pandas as pd
import os
from glob import glob

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