#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic dash application to explore the errors of the Pix2Pix network depending on input and tide conditions.

Created on Tue Jun 14 13:18:31 2022

@author: Aurelien Callens
"""
import pickle
import bz2file as bz2
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_core_components as dcc
import dash_html_components as html
from dash import Dash
from dash.dependencies import Output, Input

def color_vec(df, i):
    vec = np.repeat('blue', len(df))
    vec[i] = 'red'
    return(vec)

data = bz2.BZ2File('df.pbz2', 'rb')
df = pickle.load(data)

app = Dash(__name__)
server = app.server

df['Err'] = list(map(lambda x: np.abs(df['true'][x].squeeze() - df['pred'][x]), range(len(df))))

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children="Absolute error analysis", style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            dcc.Dropdown(id='bathy',
                         options=[{'label': i, 'value': i} for i in df['bathy'].unique()],
                         value='2017-03-27'),
            dcc.Slider(id='slider_i',
                       value=0,
                       min=0,
                       tooltip={"placement": "bottom", "always_visible": True})
           ],style={'width': '60%', 'margin':'auto', 'justify-content': 'center'})
        ]),
        html.H3([html.P(id='metrics')], style=dict(display='flex', justifyContent='center')),
        html.Div(dcc.Graph(id='plotly'), style={'width': '100%', 'display': 'inline-block', 'align-items': 'center', 'justify-content': 'center'})
    ])

@app.callback(
    Output('slider_i', component_property='max'),
    Input('bathy', 'value')
)
def update_slider(bathy):
    dff = df[df['bathy'] == str(bathy)].reset_index()
    return len(dff)-1

@app.callback(
    Output('plotly', 'figure'),
    Input('bathy', 'value'),
    Input('slider_i', 'value'),)
def update_graph(bathy, index):
    dff = df[df['bathy'] == str(bathy)].reset_index()

    i = int(index)

    fig = make_subplots(2, 3,
                        subplot_titles=('Snap Input', 'Timex Input', 'Tide level', 
                                        'True Bathy', 'Pred. Bathy', 'Absolute error map'))

    _vmin, _vmax = np.min(dff['true'][i])-1, np.max(dff['true'][i])+1

    fig.add_trace(
        go.Heatmap(z=dff['input'][i][:,:,0], colorscale='gray', showscale=False), row=1, col=1)

    fig.add_trace(
        go.Heatmap(z=dff['input'][i][:,:,1], colorscale='gray', showscale=False), row=1, col=2)

    fig.add_trace(
        go.Scatter(mode='markers', x=dff['Date'], y=dff['Tide'], marker=dict(size=10, color=color_vec(dff,i))), row=1, col=3)

    fig.add_trace(
        go.Heatmap(z=dff['true'][i].squeeze(), colorscale='jet', colorbar=dict(x=0.29, y=0.2, len=.4), zmin=_vmin, zmax=_vmax), row=2, col=1)

    fig.add_trace(
        go.Heatmap(z=dff['pred'][i], colorscale='jet', colorbar=dict(x=0.645, y=0.2, len=.4) , zmin=_vmin, zmax=_vmax), row=2, col=2)

    fig.add_trace(
        go.Heatmap(z=dff['Err'][i], colorscale='inferno', colorbar=dict(x=1, y=0.2, len=.4)), row=2, col=3)
    fig.update_layout(plot_bgcolor = "white", transition_duration=10)
    fig.update_layout(autosize=True, height=1000)
    return fig



@app.callback(
    Output('metrics', 'children'),
    Input('bathy', 'value'),
    Input('slider_i', 'value'),)
def update_metric(bathy, index):
    dff = df[df['bathy'] == str(bathy)].reset_index()

    i = int(index)

    sentence = 'RSME: {rmse:.2f}, MAE: {mae:.2f}'.format(rmse=dff['rmse'][i], mae=dff['mae'][i])
    return sentence

if __name__ == '__main__':
    app.run_server(debug=True)
