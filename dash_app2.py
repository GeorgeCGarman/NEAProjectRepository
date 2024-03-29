import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import sqlite3
import json
import pandas as pd
import main

TWITTER_ACCOUNTS = main.TWITTER_ACCOUNTS
COLOURS = main.COLOURS
con = sqlite3.connect("twitterDB.db")
con.row_factory = lambda cursor, row: row[0]
cursor = con.cursor()
uk_regions = json.load(open("ukcounties.json", 'r'))  # Convert the geojson (json describing the shapes of the
# sub-regions) into a dictionary

def run_dash_app():
    def get_scatter_data(region_name):  # returns the data values for the scatter graph
        con = sqlite3.connect("twitterDB.db")
        scatter_df = pd.read_sql_query("SELECT text, polarity, created_at "
                                       "FROM Tweets "
                                       "WHERE region_name='{}' ".format(region_name), con)  # Get the text, polarity,
        # and date created of all tweets in this region

        #scatter_df['created_at'] = scatter_df['created_at'].apply(to_datetime)
        scatter_df['text'] = scatter_df['text'].str.wrap(30)
        scatter_df['text'] = scatter_df['text'].apply(lambda x: x.replace('\n', '<br>'))
        data = go.Scatter(x=scatter_df['created_at'], y=scatter_df['polarity'],
                          mode='markers', hoverinfo='text', text=scatter_df['text'])
        return data

    def get_map_df():
        d = {'region_name': [], 'overall_sent': []}
        count = 0
        for feature in uk_regions['features']:  # Loops through geojson, which is a collection of shapes called 'features'
            feature['id'] = feature['properties']['NAME_2']  # Gives this feature a new id field set to the name of the
            # sub-region
            region_name = feature['id']
            overall_sent = cursor.execute("""SELECT SUM(polarity)
                                            FROM Tweets
                                            WHERE region_name = '{}'""".format(region_name)).fetchall()[0]

            if overall_sent is None:
                overall_sent = 0.0
            d['region_name'].append(region_name)
            d['overall_sent'].append(overall_sent)
            count += 1

        df = pd.DataFrame(data=d)  # df holds the overall sentiment polarity for each sub-region
        max_overall_sent = max(map(abs, df['overall_sent']))
        df['overall_sent'] = df['overall_sent'] / max_overall_sent  # scale all overall sents down so that the largest
        # one (positive or negative) = 1
        return df

    map_df = get_map_df()
    my_map = go.Choroplethmapbox(  # Creates the map.
        geojson=uk_regions,
        locations=map_df['region_name'],
        # The locations parameter takes the ids of the features in the geojson that will be rendered
        z=map_df['overall_sent'],  # takes in the color values for the regions
        zmin=-1,
        zmax=1,
        colorscale=["red", "white", "blue"],
        marker_line_width=0.5,
    )

    app = dash.Dash()  # setup a dash app

    map_fig = go.Figure(my_map)
    map_fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360}, height=700)

    app.layout = html.Div(className='row',  # creates html div with the map and the graph side-by-side.
                          style={'display': 'flex'},
                          children=[html.Div(dcc.Graph(id='map_fig', figure=map_fig, config={'displayModeBar': False})),
                                    html.Div([dcc.Graph(id='my_scatter', config={'displayModeBar': False})],
                                            style={'width':'50%', 'float':'right'})])
    # html.Div(html.Pre(id='hover-data', style={'paddingTop': 35}),
    #          style={'width': '30%'})

    @app.callback(Output('my_scatter', 'figure'),
                  [Input('map_fig', 'clickData')])
    def update_graph(clickData):  # Gets called whenever a region on the map is clicked
        location = clickData['points'][0]['location']  # Get the name of the region
        data = get_scatter_data(location)  # Get the data for that region
        new_fig = {'data': [data], 'layout':go.Layout(title='Tweets from {}'.format(location), hovermode='closest')}
        return new_fig # Returns a new figure

    @app.callback(Output('hover-data', 'children'),
                  [Input('my_scatter', 'hoverData')])
    def callback_hover(hoverData):
        text = json.dumps(hoverData['points'][0]['text'])
        return text

    app.run_server()

def week_to_date(week):
    items = week.split('-')
    day = str(int(items[-1]) * 7)
    date = items[0]+'-'+items[1]+'-'+day
    return date

def overview(app):
    drop_down_opt = []
    drop_down_opt.append({'label': 'All', 'value': 'All'})
    for account in TWITTER_ACCOUNTS:
        drop_down_opt.append({'label': account, 'value': account})
    con.row_factory = lambda cursor, row: row
    df = pd.read_sql("SELECT * FROM Weeks", con)
    grouped = df.groupby(['operator_name', 'week'])
    # agged = grouped.agg(overall_sent=pd.NamedAgg(column='overall_sent', aggfunc=sum)).reset_index()
    agged = grouped\
            .agg(tweet_count=('overall_sent', 'count'), overall_sent=('overall_sent', 'sum'))\
            .reset_index()
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(agged)
    max_overall_sent = max(map(abs, agged['overall_sent']))
    agged['overall_sent'] = agged['overall_sent'] /  max_overall_sent
    agged['week'] = agged['week'].apply(week_to_date)

    line_fig = go.Figure()
    for name, group in agged.groupby('operator_name'):
        trace = go.Scatter(x=group['week'].tolist(), y=group['overall_sent'].tolist())
        print(name)
        trace.name = name
        color = COLOURS[TWITTER_ACCOUNTS.index(name)]
        trace.line = dict(color=color)
        line_fig.add_trace(trace)
    line_fig.update_layout(title='Overall sentiment by week')

    piedf = agged.groupby('operator_name').agg(tweet_count=('tweet_count', 'sum')).reset_index()
    print(piedf.head())
    labels = piedf['operator_name']
    values = piedf['tweet_count']
    pie_fig = go.Figure(data=go.Pie(labels=labels, values=values))
    #pie_fig.update_traces(marker=dict(colors=COLOURS))
    pie_fig.update_layout(title='Tweet share')

    app.layout = html.Div([html.H1('Network Performance Tracker', style={'font-family': 'verdana'}),
                           html.Div([html.Label(['Track ', dcc.Dropdown(id='network-dropdown',
                                        options=drop_down_opt,
                                        style={'font-family': 'verdana', 'width': '200px', 'display': 'inline-block'},
                                        value={'label': 'All', 'value': 'All'})], style={'font-family': 'verdana'}),
                                    html.Button('Get data', id='get-data-button', n_clicks=0, style={'font-family': 'verdana', 'display': 'table-cell'})],
                                    style=dict(width = '30%',display = 'table')),
                           dcc.Graph('line-graph', figure=line_fig),
                           dcc.Graph('pie-chart', figure=pie_fig)], id='page-content')
    #fig.update_layout(title_font_family="Open Sans")

app = dash.Dash()
overview(app)
app.run_server()



# @app.callback(Output('line-graph', 'figure'),
#               Input('network-dropdown', 'value'))
# def update_line_graph(value):
#
