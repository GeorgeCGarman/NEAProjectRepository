import json
import pandas as pd
import plotly.graph_objects as go
import dataset
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import sqlite3
from datetime import datetime
import numpy as np
db = dataset.connect("sqlite:///twitterDB.db")

uk_regions = json.load(open("ukcounties.json", 'r'))
d = {'id': [], 'tweets': [], 'averageSent': [], 'count': []}



def get_scatter_data(region_name):
    con = sqlite3.connect("twitterDB.db")
    df = pd.read_sql_query("SELECT text, polarity, created_at "
                           "FROM Tweets "
                           "WHERE region_name='{}' ".format(region_name), con)
    def to_datetime(dtime):
        return datetime.strptime(dtime,'%a %b %d %H:%M:%S +0000 %Y') #.date()

    df['created_at'] = df['created_at'].apply(to_datetime)
    data = go.Scatter(x=df['created_at'], y=df['polarity'], mode='markers')
    # fig = px.scatter(df, x="created_at",
    #                  y="polarity",
    #                  title="Tweets",
    #                  hover_data="text")
    # fig.update_traces(text=df['text'])
    #fig.show()
    return data

def make_map():
    for feature in uk_regions['features']:
        feature['id'] = feature['properties']['NAME_2']

        d['id'].append(feature['id'])
        table = db['Tweets']
        results = table.find(region_name=feature['id'])
        totalSent = 0
        count = 0
        fulltext = ''
        for result in results:
            totalSent += result['polarity']
            count += 1
            text = result['text']
            fulltext += "\n"+text

        d['tweets'].append(fulltext)
        d['count'].append(count)
        if count > 0:
            averageSent = totalSent/count
            d['averageSent'].append(averageSent)
        else:
            d['averageSent'].append(0.0)

    df = pd.DataFrame(d)

    fig = go.Figure(go.Choroplethmapbox(geojson=uk_regions, locations=df['id'],
                               z=df['averageSent'], zmin=-1, zmax=1,
                               colorscale= ["red", "white", "blue"], #[(0,"red"), (0.4,"lightred"), (0.5,"yellow"), (0.6,"lightgreen"), (1,"green")],
                               marker_line_width=0.5,
                               )) #text=df['count']

    fig.update_layout(mapbox_style="carto-positron",
                    mapbox_zoom=4, mapbox_center = {"lat": 55.3781, "lon": -3.4360})
    #fig.show()
    app = dash.Dash()
    app.layout = html.Div([dcc.Graph(id='map',
                                     figure=fig),
                           #html.Div([html.Pre(id='hover-data', style={'paddingTop':35})], style={'width':'30%'})
                           dcc.Graph(id='scatter')
                           ])

    @app.callback(Output('scatter','figure'),
                  [Input('map', 'clickData')])
    def update_graph(clickData):
        location = clickData['points'][0]['location']
        data = get_scatter_data(location)
        return {'data': [data], 'layout': {'title': 'Tweets from {}'.format(location)}}

    app.run_server()


