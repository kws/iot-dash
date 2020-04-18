import os
import sqlite3
from datetime import datetime, timedelta
from pytz import timezone
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
            "select l.date,l.id,s.name,l.type,l.value,s.sort_order from log as l"
            "  left join sensors as s on l.id = s.id "
            "  where l.date>=? and l.type=? order by l.date",
            conn, params=[start, type])

    df['date'] = pd.to_datetime(df.date)
    df['date'] = df['date'].dt.tz_localize(timezone('UTC'))
    df['date'] = df['date'].dt.tz_convert(__TIMEZONE)

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


def _gantt_grouper(start_date_tz, days):
    if days <= 1/12:
        time_window = 1
    elif days <= 1:
        time_window = 5
    elif days <= 7:
        time_window = 15
    else:
        time_window = 30

    def grouper(df):
        dummies = df[~df.dummy_row.isnull()]
        df = df[df.dummy_row.isnull()].copy()

        df = df.sort_values("date").reset_index(drop=True)
        df.loc[df.value == '1', 'start'] = df.date
        df.loc[df.value == '0', 'end'] = df.date
        df[['end']] = df[['end']].fillna(method='bfill')
        df[['start']] = df[['start']].fillna(method='ffill')

        df.loc[df.start.isnull(), 'start'] = start_date_tz
        df.loc[df.end.isnull(), 'end'] = start_date_tz + timedelta(days=days)

        df['delta'] = df['start'] + timedelta(minutes=time_window)
        df['delta_prev'] = df.delta.shift(1)
        df.loc[df.delta_prev.isnull(), 'delta_prev'] = df.delta

        df.loc[(df.start <= df.delta_prev), 'delta'] = df.delta_prev

        df['end'] = df[['end', 'delta']].max(axis=1)
        df['prev_end'] = df.end.shift(1)
        df.loc[df.prev_end.isnull(), 'prev_end'] = start_date_tz
        df['group_id'] = df.index
        df.loc[df.start <= df.prev_end, 'group_id'] = np.nan
        df['group_id'] = df['group_id'].fillna(method='ffill')

        df = df.groupby('group_id').agg({
            'name': 'first',
            'start': min,
            'end': max,
            'sort_order': 'first'
        }).reset_index()
        df = pd.concat([dummies, df])

        df = df[["name", "start", "end", "sort_order"]]
        df.columns = ["Task","Start","Finish","Sort"]

        return df
    return grouper


def value_gantt(type, days=None):
    df = get_data(type, days=days)

    # Make sure we show all sensors even if no data
    sensors = get_sensors(type)
    sensors = pd.DataFrame(sensors)
    sensors['dummy_row'] = True
    start_date = datetime.utcnow() - timedelta(days=days)
    start_date = timezone('UTC').localize(start_date)
    start_date = start_date.astimezone(__TIMEZONE)
    sensors['date'] = start_date
    sensors['value'] = '1'
    df = pd.concat([df, sensors])
    sensors['date'] = start_date + timedelta(seconds=0.1)
    sensors['value'] = '0'
    df = pd.concat([df, sensors])

    df = df.groupby("id").apply(_gantt_grouper(start_date, days)).reset_index()
    del df["level_1"]

    df = df.sort_values(by=["Sort", "Start","Task"])

    if df.shape[0] == 0:
        return {}

    fig = ff.create_gantt(df, group_tasks=True, index_col='Task')
    fig.layout.xaxis.range = (datetime.now() - timedelta(days=days), datetime.now())
    return fig

