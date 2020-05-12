import os
import sqlite3
from datetime import datetime, timedelta
from pytz import timezone, tzinfo, UTC
import pandas as pd
import numpy as np
import plotly.figure_factory as ff

__DEFAULT_DAYS = 1

_DB_URL = os.getenv("IOT_DB_URL")

__TIMEZONE = timezone('Europe/London')


def get_data(type, days=None):
    if days is None:
        days = __DEFAULT_DAYS

    start_date = datetime.utcnow() - timedelta(days=days)
    start = start_date.strftime('%Y-%m-%dT%H:%M:%S')

    with sqlite3.connect(_DB_URL) as conn:
        df = pd.read_sql_query(
            "select l.date,l.id,s.name,"
            "  l.type,l.value,s.sort_order from log as l"
            "  left join sensors as s on l.id = s.id "
            "  where l.date>=? and l.type=? order by l.date",
            conn, params=[start, type])

    df['date'] = pd.to_datetime(df.date)
    df['date'] = df['date'].dt.tz_localize(timezone('UTC'))
    df['date'] = df['date'].dt.tz_convert(__TIMEZONE)
    df.loc[df.name.isna(), 'name'] = df.id.apply(lambda x: f'Sensor {x}')
    df.loc[df.sort_order.isna(), 'sort_order'] = "zzz"
    return df


def get_sensors(type):
    with sqlite3.connect(_DB_URL) as conn:
        c = conn.cursor()
        r = c.execute("select id, name, sort_order, type from sensors where type=? order by sort_order", [type])
        data = r.fetchall()

    return [dict(id=r[0], name=r[1], sort_order=r[2], type=r[3]) for r in data]

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


def value_gantt(type, days=None):
    df = get_data(type, days=days)

    if days <= 1/12:
        time_window = 1
    elif days <= 1:
        time_window = 5
    elif days <= 7:
        time_window = 15
    else:
        time_window = 30

    start_date = datetime.utcnow() - timedelta(days=days)
    start_date_tz = UTC.localize(start_date)

    # Create start and end times
    df = df.sort_values(["id", "date"]).reset_index(drop=True)
    df.loc[df.value == '1', 'start'] = df.date
    df.loc[df.value == '0', 'end'] = df.date

    # Fill first and last of each sensor with the start and end of dataframe
    df.loc[(df.start.isnull()) & (df.id != df.id.shift(1)), 'start'] = start_date_tz
    df.loc[(df.end.isnull()) & (df.id != df.id.shift(-1)), 'end'] = start_date_tz + timedelta(days=days)

    df[['end']] = df[['end']].fillna(method='bfill')
    df[['start']] = df[['start']].fillna(method='ffill')

    # Set minimum length
    df['delta'] = df['start'] + timedelta(minutes=time_window)
    df['delta_prev'] = df.delta.shift(1)
    next_sensor = df.id != df.id.shift(1)
    df.loc[next_sensor, 'delta'] = df.end
    df.loc[next_sensor, 'delta_prev'] = df.start - timedelta(seconds=1)

    # Group them
    df['group_id'] = df.index
    df.loc[df.start <= df.delta_prev, 'group_id'] = np.nan
    df['group_id'] = df['group_id'].fillna(method='ffill')

    # And merge
    df = df.groupby('group_id').agg({'name': 'first', 'start': min, 'end':max, 'sort_order': 'first'}).reset_index()

    # Make sure we show all sensors even if no data
    sensors = get_sensors(type)
    sensors = pd.DataFrame(sensors)
    sensors['start'] = start_date_tz
    sensors['end'] = start_date_tz + timedelta(seconds=0.1)

    df = pd.concat([df, sensors])

    df = df[["name", "start", "end", "sort_order"]]
    df.columns = ["Task", "Start", "Finish", "Sort"]

    df = df.sort_values(by=["Sort", "Start","Task"])

    fig = ff.create_gantt(df, group_tasks=True, index_col='Task')
    fig.layout.xaxis.range = (datetime.now() - timedelta(days=days), datetime.now())
    return fig

