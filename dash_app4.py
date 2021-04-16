import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

import sqlite3
import json
import pandas as pd
import main


TWITTER_ACCOUNTS = main.TWITTER_ACCOUNTS
COLOURS = main.COLOURS
DB = main.DB

uk_regions = json.load(open("ukcounties.json", 'r'))  # Convert the geojson (json describing the shapes of the


# sub-regions) into a dictionary


def week_to_date(week):
    items = week.split('-')
    day = str((int(items[-1]) * 7) + 1)
    date = items[0] + '-' + items[1] + '-' + day
    return date


def main_layout():
    drop_down_opt = [{'label': 'All',
                      'value': 'All'}]  # Creating the drop-down menu with a separate option for each network operator
    for account in TWITTER_ACCOUNTS:
        drop_down_opt.append({'label': account, 'value': account})  # Fill the drop-down with the twitter account names

    # Setting up the page with a title, drop-down menu, and button
    layout = [html.H1('Network Performance Tracker', style={'font-family': 'verdana'}),
              html.Div([html.Label(['Track ', dcc.Dropdown(id='network-dropdown',
                                                           options=drop_down_opt,
                                                           style={'font-family': 'verdana', 'width': '200px',
                                                                  'display': 'inline-block'},
                                                           value='All')],
                                   style={'font-family': 'verdana'}),
                        html.Button('Get data', id='get-data-button', n_clicks=0,
                                    style={'font-family': 'verdana', 'fontSize': 24, 'display': 'table-cell'})],
                       style=dict(width='30%', display='table'))]

    return layout


def overview():
    con = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM Weeks", con)  # Get all the data from Weeks
    con.close()
    df = df.groupby(['operator_name', 'week'])  # Group the data into operator name then week
    df = df.agg(tweet_count=('overall_sent', 'count'), overall_sent=('overall_sent', 'mean')) \
        .reset_index()  # Create two new columns which hold the count and the overall sentiment from each week
    print(df.head())

    # max_overall_sent = max(map(abs, df['overall_sent']))
    # df['overall_sent'] = df['overall_sent'] / max_overall_sent  # Normalize the overall sentiments between -1 and 1
    df['week'] = df['week'].apply(week_to_date)  # Turn all the weeks back to dates by replacing them with the date of
    # the first day in that week. This means a time series graph can be created.

    line_fig = go.Figure()  # Creating the line chart
    for name, group in df.groupby('operator_name'):  # Loop over each operator
        trace = go.Scatter(x=group['week'].tolist(), y=group['overall_sent'].tolist())
        trace.name = name
        color = COLOURS[name]  # Select the corresponding colour for the region
        trace.line = dict(color=color)
        line_fig.add_trace(trace)
    line_fig.update_layout(title='Overall Sentiment by Week')

    # line_fig.update_yaxes(range=[1, -1])

    pie_df = df.groupby('operator_name').agg(tweet_count=('tweet_count', 'sum')).reset_index()  # Get the count of the
    # tweets for each operator
    labels = pie_df['operator_name']
    values = pie_df['tweet_count']
    colors = pie_df['operator_name'].map(COLOURS)
    pie_fig = go.Figure(data=go.Pie(labels=labels, values=values))  # Create the pie chart
    pie_fig.update_traces(marker=dict(colors=colors))
    pie_fig.update_layout(title='Tweet Share')

    # layout describes the layout of the web-page.
    layout = [dcc.Graph('line-graph', figure=line_fig, config={'displayModeBar': False},
                        style={'display': 'flex', 'height': '80vh'}),
              dcc.Graph('pie-chart', figure=pie_fig, config={'displayModeBar': False},
                        style={'display': 'flex', 'height': '80vh'})]
    return layout


def account_view(operator_name):
    map_fig = create_map(operator_name)
    rank_table = create_rank_table(operator_name)
    layout = html.Div(className='row',
                      style={'display': 'flex', 'height': '80vh'},
                      children=[dcc.Graph('map', figure=map_fig, config={'displayModeBar': False}),
                                html.Div(id='detail', children=dcc.Graph('rank-table', figure=rank_table,
                                                                         config={'displayModeBar': False}))])
    return layout


def create_map(operator_name):
    d = {'region_name': [], 'overall_sent': []}
    count = 0
    con = sqlite3.connect(DB)
    con.row_factory = lambda cursor, row: row[0]
    cur = con.cursor()
    for feature in uk_regions['features']:  # Loops through geojson, which is a collection of shapes called 'features'
        feature['id'] = feature['properties']['NAME_2']  # Gives this feature a new id field set to the name of the
        # sub-region, which is used so that Plotly can plot the choropleth map
        region_name = feature['id']
        overall_sent = cur.execute("""SELECT SUM(polarity)
                                      FROM Tweets, TweetOperator
                                      WHERE Tweets.tweet_id = TweetOperator.tweet_id
                                      AND Tweets.region_name = '{}'
                                      AND TweetOperator.operator_name = '{}'""".format(region_name,
                                                                                       operator_name)).fetchall()[0]
        # The above query gets the total sentiment polarity of every tweet within that region (within the last week) that is about the
        # given network operator

        if overall_sent is None:
            overall_sent = 0.0
        d['region_name'].append(region_name)
        d['overall_sent'].append(overall_sent)
        count += 1

    # print(pd.DataFrame(data=d).head())
    # print('count:', len(pd.DataFrame(data=d).index))

    map_df = pd.DataFrame(data=d)  # df holds the overall sentiment polarity for each sub-region
    max_overall_sent = max(map(abs, map_df['overall_sent']))
    map_df['overall_sent'] = map_df[
                                 'overall_sent'] / max_overall_sent  # scale all overall sentiments down so that the
    # largest is 1 or -1

    print('max value:', max(map_df['overall_sent']))

    map_fig = go.Figure(data=go.Choroplethmapbox(geojson=uk_regions,  # Creating the map figure
                                                 locations=map_df['region_name'],
                                                 # The locations property takes the ids of the features in the
                                                 # geojson that will be rendered
                                                 z=map_df['overall_sent'],  # takes in the color values for the regions
                                                 zmin=-1,
                                                 zmax=1,
                                                 colorscale=["red", "white", "blue"],
                                                 marker_line_width=0.5))
    map_fig.update_layout(title='Tweet Sentiment by County',
                          mapbox_style="carto-positron",
                          mapbox_zoom=4, mapbox_center={"lat": 55.3781, "lon": -3.4360})
    return map_fig


def create_rank_table(operator_name):
    con = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM Weeks WHERE operator_name='{}'".format(operator_name), con)
    con.close()
    df = df.groupby(['region_name'])
    df = df.agg(tweet_count=('overall_sent', 'count'), overall_sent=('overall_sent', 'sum')) \
        .reset_index()
    max_overall_sent = max(map(abs, df['overall_sent']))
    df['overall_sent'] = df['overall_sent'] / max_overall_sent
    df['rank'] = df['overall_sent'].rank(ascending=0).astype(int)
    print(df.head())

    df = df.sort_values(by=['rank'])
    cols = ['rank', 'region_name', 'overall_sent']
    df = df[cols]
    rank_table = go.Figure(data=[go.Table(
        header=dict(values=['Rank', 'County', 'Overall sentiment'],
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[df['rank'], df['region_name'], df['overall_sent']],
                   fill_color='lavender',
                   align='left'))
    ])
    con.close()
    rank_table.update_layout(title='Regional Rankings')
    layout = [dcc.Graph('rank-table', figure=rank_table, config={'displayModeBar': False},
                        style={'display': 'flex', 'height': '80vh'})]
    return layout


def create_scatter(region_name, operator_name):
    con = sqlite3.connect(DB)
    scatter_df = pd.read_sql_query("SELECT text, polarity, created_at "
                                   "FROM Tweets, TweetOperator "
                                   "WHERE Tweets.tweet_id = TweetOperator.tweet_id"
                                   "      AND Tweets.region_name='{}' "
                                   "      AND TweetOperator.operator_name='{}'".format(region_name, operator_name),
                                   con)  # Get the text, polarity,
    # and date created of all tweets in this region

    scatter_df['text'] = scatter_df['text'].str.wrap(30) # keep the text of the tweets within a text box of width 30
    scatter_df['text'] = scatter_df['text'].apply(lambda x: x.replace('\n', '<br>')) # replace \n with the html <br>
    scatter_fig = go.Figure(go.Scatter(x=scatter_df['created_at'], y=scatter_df['polarity'],
                                       mode='markers', hoverinfo='text', text=scatter_df['text']))
    scatter_fig.update_layout(yaxis_range=[-1, 1])
    return scatter_fig


app = dash.Dash()

app.layout = html.Div(children=[html.Div(id='main-layout', children=main_layout()),
                                html.Div(id='page-content', children=overview()),
                                html.Div(id='placeholder')])


@app.callback([Output('detail', 'children')],
              [Input('map', 'clickData')],
              [State('network-dropdown', 'value')]) # store the state of of the drop-down menu
def update_region(clickData, value):  # Gets called whenever a region on the map is clicked
    operator_name = value
    if clickData is None: # if it gets called without a given region, display the account view
        return create_rank_table(operator_name)
    region_name = clickData['points'][0]['location']  # Get the name of the region
    scatter_fig = create_scatter(region_name, operator_name)
    scatter_fig.update_layout(title="Tweets from {}".format(region_name),
                              xaxis_title="Time",
                              yaxis_title="Sentiment Polarity")
    layout = [html.Div(dcc.Graph('scatter', figure=scatter_fig, config={'displayModeBar': False}))]
    return layout  # Returns a new figure


@app.callback(Output('page-content', 'children'),
              [Input('network-dropdown', 'value')])
def update_account(value):
    if value == 'All':
        return overview()
    else:
        return account_view(value)


@app.callback(Output('placeholder', 'children'),
              [Input('get-data-button', 'n_clicks')])
def update_data(n_clicks):
    if n_clicks == 0: return
    main.get_data()
    main.condense_db()
    return None


app.run_server()
