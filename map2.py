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
        scatter = go.Scatter(x=scatterdf['created_at'], y=scatterdf['polarity'],
                             mode='markers', hoverinfo='none', text=scatterdf['text'])
        return scatter

    d = {'id': [], 'avg_sent': [], 'overall_sent': [], 'count': []}
    for feature in uk_regions['features']:
        feature['id'] = feature['properties']['NAME_2']
        d['id'].append(feature['id'])
        region_name = feature['id']
        # d['name'].append(region_name)  # Append the name of the subregion to the name field of the dict
        tweet_sents = cursor.execute("SELECT polarity "
                                     "FROM Tweets "
                                     "WHERE region_name='{}' ".format(region_name)).fetchall()
        overall_sent = 0
        count = 0
        for sent in tweet_sents:  # Calculating average sentiment polarity
            overall_sent += sent
            count += 1
        d['count'].append(count)

        if count > 0:
            avg_sent = overall_sent / count
            d['avg_sent'].append(avg_sent)
        else:
            d['avg_sent'].append(0.0)
        d['overall_sent'].append(overall_sent)

    df = pd.DataFrame(d)
    max_overall_sent = max(map(abs, df['overall_sent']))
    df['normal_avg_sent'] = df['overall_sent'] / max_overall_sent

    map_figure = go.Choroplethmapbox(
        geojson=uk_regions,
        locations=df['id'],
        z=df['normal_avg_sent'],
        zmin=-1,
        zmax=1,
        colorscale=["red", "white", "blue"],
        marker_line_width=0.5,
    )

    app = dash.Dash()

    fig = go.Figure(map_figure)
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360})
    # fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'mapbox'},{'type': 'xy'}]])
    # app.layout = html.Div([dcc.Graph(id='fig',
    #                                   figure=fig),
    #                        dcc.Graph(id='my_scatter')
    #                         ])
    app.layout = html.Div(className='row',
                          style={'display': 'flex'},
                          children=[html.Div(dcc.Graph(id='fig', figure=fig)),
                                    html.Div([dcc.Graph(id='my_scatter'),
                                             html.Div(html.H1(id='tweet text', style={'paddingTop': 35, 'fontSize':25, 'display': 'inline-block', 'max-width':'100%'}), style={'width':'100%'})]
                        )])


    @app.callback(Output('tweet text','children'),
                    [Input('my_scatter','hoverData')])
    def callback_hover(hoverData):
        text = hoverData['points'][0]['text']
        return json.dumps(text)

    @app.callback(Output('my_scatter', 'figure'),
                  [Input('fig', 'clickData')])
    def update_graph(clickData):
        location = clickData['points'][0]['location']
        data = get_scatter_data(location)
        return {'data': [data], 'layout': {'title': 'Tweets from {}'.format(location)}}

    app.run_server()


make_map()
