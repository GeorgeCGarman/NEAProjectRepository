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
# con = sqlite3.connect("twitterDB.db")
# # con.row_factory = lambda cursor, row: row[0]
# cursor = con.cursor()
uk_regions = json.load(open("ukcounties.json", 'r'))  # Convert the geojson (json describing the shapes of the


# sub-regions) into a dictionary
# con.close()

def week_to_date(week):
    items = week.split('-')
    day = str(int(items[-1]) * 7)
    date = items[0] + '-' + items[1] + '-' + day
    return date


def main_layout():
    drop_down_opt = [{'label': 'All',
                      'value': 'All'}]  # Creating the drop-down menu with a separate option for each network operator
    for account in TWITTER_ACCOUNTS:
        drop_down_opt.append({'label': account, 'value': account})

    layout = html.Div([html.H1('Network Performance Tracker', style={'font-family': 'verdana'}),
                       html.Div([html.Label(['Track ', dcc.Dropdown(id='network-dropdown',
                                                                    options=drop_down_opt,
                                                                    style={'font-family': 'verdana', 'width': '200px',
                                                                           'display': 'inline-block'},
                                                                    value='All')], style={'font-family': 'verdana'}),
                                 html.Button('Get data', id='get-data-button', n_clicks=0,
                                             style={'font-family': 'verdana', 'display': 'table-cell'})],
                                style=dict(width='30%', display='table'))])

    return layout


def overview():
    con = sqlite3.connect("twitterDB.db")
    df = pd.read_sql("SELECT * FROM Weeks", con)  # Get all the data from Weeks
    con.close()
    df = df.groupby(['operator_name', 'week'])  # Group the data into operator name then week
    df = df.agg(tweet_count=('overall_sent', 'count'), overall_sent=('overall_sent', 'sum')) \
        .reset_index()  # Create two new columns which hold the count and the overall sentiment from each week
    max_overall_sent = max(map(abs, df['overall_sent']))
    df['overall_sent'] = df['overall_sent'] / max_overall_sent  # Normalize the overall sentiments between -1 and 1
    df['week'] = df['week'].apply(week_to_date)  # Turn all the weeks back to dates by replacing them with the date of
    # the first day in that week. This means a time series graph can be created.

    line_fig = go.Figure()  # Creating the line chart
    for name, group in df.groupby('operator_name'):  # Loop over each operator
        trace = go.Scatter(x=group['week'].tolist(), y=group['overall_sent'].tolist())
        trace.name = name
        color = COLOURS[TWITTER_ACCOUNTS.index(name)]
        trace.line = dict(color=color)
        line_fig.add_trace(trace)
    line_fig.update_layout(title='Overall sentiment by week')

    pie_df = df.groupby('operator_name').agg(tweet_count=('tweet_count', 'sum')).reset_index()  # Get the count of the
    # tweets for each operator
    labels = pie_df['operator_name']
    values = pie_df['tweet_count']
    pie_fig = go.Figure(data=go.Pie(labels=labels, values=values))  # Create the pie chart
    # pie_fig.update_traces(marker=dict(colors=COLOURS)) *
    pie_fig.update_layout(title='Tweet share')

    # layout describes the layout of the web-page.
    # make content div and have the default stuff e.g. title *
    layout = html.Div(id='page-content', children=[dcc.Graph('line-graph', figure=line_fig),
                       dcc.Graph('pie-chart', figure=pie_fig)])
    return layout

app = dash.Dash()
app.layout = html.Div([main_layout(), overview()])
app.run_server()

overview()
