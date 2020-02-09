# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

from app import data

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

df = data.read_data()


def update_figure(type):
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
            yaxis={'title': 'Temperature (C)'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            transition={'duration': 500},
        )
    }


app.layout = html.Div(children=[
    html.H1(children='IOT Data'),

    html.H3(children='''
        Temperature
    '''),

    dcc.Graph(id='temp-graph', figure=update_figure('temperature')),

    html.H3(children='''
    Light Level
'''),

    dcc.Graph(id='light-graph', figure=update_figure('lightlevel'))

])

if __name__ == '__main__':
    app.run_server(debug=True)