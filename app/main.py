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
    df = data.read_data()
    return html.Div(children=[
        html.H1(children='IOT Data'),

        html.H3(children='Temperature'),

        dcc.Graph(id='temp-graph', figure=data.value_timeseries('temperature', df=df, ylabel='Temperature (C)')),

        html.H3(children='Light Level'),

        dcc.Graph(id='light-graph', figure=data.value_timeseries('lightlevel', df=df, ylabel='Level')),

        html.H3(children='Presence'),

        dcc.Graph(id='presence-graph', figure=data.value_gantt('presence', df=df)),

        dcc.Interval(
            id='interval-component',
            interval=60 * 1000,  # in milliseconds
            n_intervals=0
        )
    ])


app.layout = serve_layout


@app.callback(Output('temp-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_temperature(n):
    return data.value_timeseries('temperature', ylabel='Temperature (C)')


@app.callback(Output('light-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_temperature(n):
    return data.value_timeseries('lightlevel', ylabel='Level')


@app.callback(Output('presence-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_temperature(n):
    return data.value_gantt('presence')


if __name__ == '__main__':
    app.run_server(debug=True)
