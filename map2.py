import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

import sqlite3
import json
import pandas as pd
from datetime import datetime
con = sqlite3.connect("twitterDB.db")
con.row_factory = lambda cursor, row: row[0]
cursor = con.cursor()
uk_regions = json.load(open("ukcounties.json", 'r'))  # Convert the geojson (json describing the shapes of the
# subregions) into a dictionary

def make_map():
    d = {'id': [], 'avg_sent': [], 'count': []}
    for feature in uk_regions['features']:
        feature['id'] = feature['properties']['NAME_2']
        d['id'].append(feature['id'])
        region_name = feature['id']
        # d['name'].append(region_name)  # Append the name of the subregion to the name field of the dict
        tweet_sents = cursor.execute("SELECT polarity "
                                     "FROM Tweets "
                                     "WHERE region_name='{}' ".format(region_name)).fetchall()
        total_sent = 0
        count = 0
        for sent in tweet_sents:  # Calculating average sentiment polarity
            total_sent += sent
            count += 1
        d['count'].append(count)

        if count > 0:
            avg_sent = total_sent / count
            d['avg_sent'].append(avg_sent)
        else:
            d['avg_sent'].append(0.0)
    df = pd.DataFrame(d)
    # normal_avg_sent = (avg_sent * count)/(max_avg_sent * max_count)
    df['normal_avg_sent'] = df['avg_sent'] * df['count']
    max_avg_sent = max(map(abs, df['normal_avg_sent']))
    df['normal_avg_sent'] = df['normal_avg_sent'] / max_avg_sent
    fig = go.Figure(go.Choroplethmapbox(geojson=uk_regions, locations=df['id'],
                                        z=df['normal_avg_sent'], zmin=-1, zmax=1,
                                        colorscale=["red", "white", "blue"],
                                        marker_line_width=0.5,
                                        ))  # text=df['count']
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360})
    app = dash.Dash()
    app.layout = html.Div([dcc.Graph(id='map',
                                     figure=fig),
                           # html.Div([html.Pre(id='hover-data', style={'paddingTop':35})], style={'width':'30%'})
                           dcc.Graph(id='scatter')
                           ])

    @app.callback(Output('scatter', 'figure'),
                  [Input('map', 'clickData')])
    def update_graph(clickData):
        location = clickData['points'][0]['location']
        data = get_scatter_data(location)
        return {'data': [data], 'layout': {'title': 'Tweets from {}'.format(location)}}

    app.run_server()

def get_scatter_data(region_name):
    con = sqlite3.connect("twitterDB.db")
    df = pd.read_sql_query("SELECT text, polarity, created_at "
                           "FROM Tweets "
                           "WHERE region_name='{}' ".format(region_name), con)
    def to_datetime(dtime):
        return datetime.strptime(dtime,'%a %b %d %H:%M:%S +0000 %Y') #.date()

    df['created_at'] = df['created_at'].apply(to_datetime)
    data = go.Scatter(x=df['created_at'], y=df['polarity'], mode='markers')
    return data