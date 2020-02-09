# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
from app import data

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


def serve_layout():
    return html.Div(children=[
        html.H1(children='IOT Data'),

        dcc.Dropdown(
            id='dropdown',
            options=[
                dict(label='1h', value=1/24),
                dict(label='12h', value=12/24),
                dict(label='1d', value=1),
                dict(label='7d', value=7),
                dict(label='30d', value=30),
            ],
            value=1/24
        ),

        html.H3(children='Temperature'),

        dcc.Graph(id='temp-graph'),

        html.H3(children='Light Level'),

        dcc.Graph(id='light-graph'),

        html.H3(children='Presence'),

        dcc.Graph(id='presence-graph'),

        dcc.Interval(
            id='interval-component',
            interval=60 * 1000,  # in milliseconds
            n_intervals=0
        )
    ])


app.layout = serve_layout


@app.callback(Output('temp-graph', 'figure'),
              [Input('interval-component', 'n_intervals'), Input('dropdown', 'value')])
def update_temperature(n, days):
    return data.value_timeseries('temperature', days=days, ylabel='Temperature (C)', cache_key=n)


@app.callback(Output('light-graph', 'figure'),
              [Input('interval-component', 'n_intervals'), Input('dropdown', 'value')])
def update_temperature(n, days):
    return data.value_timeseries('lightlevel', days=days,  ylabel='Level', cache_key=n)


@app.callback(Output('presence-graph', 'figure'),
              [Input('interval-component', 'n_intervals'), Input('dropdown', 'value')])
def update_temperature(n, days):
    return data.value_gantt('presence', days=days, cache_key=n)


if __name__ == '__main__':
    app.run_server(debug=True)
