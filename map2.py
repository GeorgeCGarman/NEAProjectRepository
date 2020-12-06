import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots

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
    def get_scatter_data(region_name):
        con = sqlite3.connect("twitterDB.db")
        scatterdf = pd.read_sql_query("SELECT text, polarity, created_at "
                               "FROM Tweets "
                               "WHERE region_name='{}' ".format(region_name), con)

        def to_datetime(dtime):
            return datetime.strptime(dtime, '%a %b %d %H:%M:%S +0000 %Y')  # Converts Twitter time to a date

        scatterdf['created_at'] = scatterdf['created_at'].apply(to_datetime)
        scatter = go.Scatter(x=scatterdf['created_at'], y=scatterdf['polarity'], mode='markers')
        return scatter

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

    map_trace = go.Choroplethmapbox(
                            geojson=uk_regions,
                            locations=df['id'],
                            z=df['normal_avg_sent'],
                            zmin=-1,
                            zmax=1,
                            colorscale=["red", "white", "blue"],
                            marker_line_width=0.5,
                )

    # scatter = get_scatter_data("Greater London")
    # fig.append_trace(map_figure,1,1)
    # fig.append_trace(scatter, 1, 2)
    #

    app = dash.Dash()

    # fig = go.Figure(map_figure)
    # fig.update_layout(mapbox_style="carto-positron",
    #                   mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360})
    # fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'mapbox'},{'type': 'xy'}]])
    # app.layout = html.Div([dcc.Graph(id='fig',
    #                                  figure=fig),
    #                        dcc.Graph(id='my_scatter')
    #                         ], style={'display': 'inline-block'})
    data = get_scatter_data('Greater London')
    scatter_trace = go.Figure({'data': [data],'layout': {'title': 'Tweets from {}'.format('Greater London')}})
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'mapbox'}, {'type': 'xy'}]])
    fig.append_trace(map_trace, 1, 1)
    fig.append_trace(scatter_trace, 1, 2)

    @app.callback(Output('my_scatter', 'figure'),
                  [Input('fig', 'clickData')]
                  [State('fig','figure')])
    def update_graph(clickData,figure):
        location = clickData['points'][0]['location']
        data = get_scatter_data(location)
        figure.data[1] = data
        #return {'data': [data], 'layout': {'title': 'Tweets from {}'.format(location)}}
        return figure

    app.run_server()

make_map()