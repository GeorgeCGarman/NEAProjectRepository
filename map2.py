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
cursor = con.cursor()
uk_regions = json.load(open("ukcounties.json", 'r'))  # Convert the geojson (json describing the shapes of the
# sub-regions) into a dictionary

def make_map():
    def get_scatter_data(region_name):  # returns the data values for the scatter graph
        con = sqlite3.connect("twitterDB.db")
        scatter_df = pd.read_sql_query("SELECT text, polarity, created_at "
                                       "FROM Tweets "
                                       "WHERE region_name='{}' ".format(region_name), con)

        def to_datetime(dtime):
            return datetime.strptime(dtime, '%a %b %d %H:%M:%S +0000 %Y')  # Converts Twitter time to a date in the
            # form yyyy-mm-dd hh:mm:ss

        scatter_df['created_at'] = scatter_df['created_at'].apply(to_datetime)
        data = go.Scatter(x=scatter_df['created_at'], y=scatter_df['polarity'],
                          mode='markers', hoverinfo='none', text=scatter_df['text'])
        return data

    d = {'region_name': [], 'overall_sent': []}
    # mylist = cursor.execute("""SELECT region_name, SUM(polarity)
    #                         FROM tweets
    #                         GROUP BY region_name""").fetchall()
    # mydf = pd.DataFrame(data=mylist)
    df = pd.read_sql("""SELECT region_name, SUM(polarity) AS overall_sent
                             FROM tweets
                             GROUP BY region_name""", con)
    results = cursor.execute("""SELECT region_name, SUM(polarity) AS overall_sent
                                 FROM tweets
                                 GROUP BY region_name""").fetchall()
    print(results)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)
    for feature in uk_regions['features']:  # Loops through geojson, which is a collection of shapes called 'features'
        feature['id'] = feature['properties']['NAME_2']  # Gives this feature a new id field set to the name of the sub-region
        region_name = feature['id']
        try:
           overall_sent = cursor.execute("""SELECT SUM(polarity)
                                            FROM tweets
                                            WHERE region_name = '{}'""".format(region_name)).fetchall()
        except sqlite3.OperationalError:
            overall_sent = 0
            print('error')
        print(overall_sent)
    #     try:
    #         df['region_name'][region_name]
    #     except KeyError:
    #         df = df.append({'region_name': region_name, 'overall_sent': 0.00}, ignore_index=True)
    #         print(region_name)
    #         #df['overall_sent'].append(0.00)
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)

        # con.row_factory = lambda cur, row: row[0]  # Makes sqlite3 connection return actual values instead of tuples
        # cursor = con.cursor
        # region_name = feature['id']
        # tweet_sents = cursor.execute("SELECT polarity "
        #                              "FROM Tweets "
        #                              "WHERE region_name='{}' ".format(region_name)).fetchall()  # Get the polarity
        # from the database *** RETURN TOTAL OR AVG? with query??
        # overall_sent = 0
        # count = 0
        # for sent in tweet_sents:  # Calculating overall sentiment polarity
        #     overall_sent += sent
        #     count += 1
        #con.row_factory = lambda cursor, row: row  # reset this property
        # d['region_name'].append(feature['id'])  # appends the region name to the dictionary
        # d['overall_sent'].append(overall_sent)  # appends the region's overall_sent

    #df = pd.DataFrame(data=d)  # df holds the overall sentiment polarity for each sub-region
    max_overall_sent = max(map(abs, df['overall_sent']))
    df['overall_sent'] = df['overall_sent'] / max_overall_sent  # scale all overall sents down so that the largest one (positive or negative) = 1

    map_figure = go.Choroplethmapbox(  # Creates the map. * should this be called figure?
        geojson=uk_regions,
        locations=df['region_name'],
        # The locations parameter takes the ids of the features in the geojson that will be rendered
        z=df['overall_sent'],  # takes in the color values for the regions
        zmin=-1,
        zmax=1,
        colorscale=["red", "white", "blue"],
        marker_line_width=0.5,
    )

    app = dash.Dash()  # setup a dash app

    fig = go.Figure(map_figure)  # create the map figure ***
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360})

    app.layout = html.Div(className='row',  # creates html div with the map and the graph side-by-side.
                          style={'display': 'flex'},
                          children=[html.Div(dcc.Graph(id='fig', figure=fig)),
                                    html.Div([dcc.Graph(id='my_scatter')])])

    @app.callback(Output('my_scatter', 'figure'),
                  [Input('fig', 'clickData')])
    def update_graph(clickData):  # Gets called whenever a region on the map is clicked
        location = clickData['points'][0]['location']  # Get the name of the region *
        data = get_scatter_data(location)  # Get the data for that region
        return {'data': [data], 'layout': {'title': 'Tweets from {}'.format(location)}}  # Returns a new figure  *

    app.run_server()


make_map()
