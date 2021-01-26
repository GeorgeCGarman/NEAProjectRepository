from datetime import datetime
import pandas as pd
import sqlite3
conn = sqlite3.connect('twitterDB.db')
conn.row_factory = lambda cursor, row: row[0]
sql_cursor = conn.cursor()

year = datetime.now().year
month = datetime.now().month
day = datetime.now().day
week = day % 7
all_regions = sql_cursor.execute("""SELECT name
                                    FROM Regions""").fetchall()
conn.row_factory = lambda cursor, row: row

def week(mydate):
    mydate = datetime.strptime(mydate, '%Y-%m-%d %H:%M:%S')
    return str(mydate.year) + '-' + str(mydate.month) + '-' + str(mydate.day % 7)

df = pd.read_sql_query("""SELECT region_name, created_at, operator_name, polarity 
                          FROM Tweets, TweetOperator
                          WHERE Tweets.tweet_id=TweetOperator.tweet_id""", conn)
#2021-01-15 15:22:08
# df['week'] = df['created_at'].apply(week)
# df = df.groupby(['region_name', 'week', 'operator_name'])['polarity'].sum()
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(df)
# # print(df.head())
# print()
df['week'] = df['created_at'].apply(week)
grouped = df.groupby(['region_name', 'week', 'operator_name'])
agged = grouped.agg(overall_sent=pd.NamedAgg(column="polarity", aggfunc=sum)).reset_index()
max_overall_sent = max(map(abs, agged['overall_sent']))
agged['overall_sent'] = agged['overall_sent'] /  max_overall_sent
#print(agged.loc[agged['overall_sent'] == 1])


# for region in all_regions:
#     df = pd.read_sql_query("""SELECT polarity, created_at, operator_name
#                               FROM Tweets, TweetOperator
#                               WHERE Tweets.tweet_id=TweetOperator.tweet_id""", conn)
#     #2021-01-15 15:22:08
#     df['week'] = df['created_at'].apply(week)
#     df = df.groupby(['week', 'operator_name'])['polarity'].sum()
#     with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#         print(df)
#     # print(df.head())
#     print()

    # max_overall_sent = max(map(abs, df['overall_sent']))
    # df['overall_sent'] = df['overall_sent'] / max_overall_sent
    # min_date =
    # df = pd.read_sql_query("""SELECT SUM(polarity) as overall_sent, operator_name
    #                                 FROM Tweets, TweetOperator
    #                                 WHERE Tweets.tweet_id=TweetOperator.tweet_id
    #                                       AND Tweets.region_name="{}"
    #                                 GROUP BY TweetOperator.operator_name""".format(region), conn)
    # print(df.head())
    # tweets_df = pd.read_sql_query("""SELECT * FROM Tweets""", conn)
    # operator_df = pd.read_sql_query("""SELECT * FROM TweetOperator""", conn)
    # tweets_df.groupby('')
    # print(tweets_df.head())
    # print(operator_df.head())
    # tweets_df = pd.read_sql_query("""SELECT SUM(polarity) as overall_sent, operator_name
    #                                  FROM Tweets, TweetOperator
    #                                  GROUP BY TweetOperator.operator_name""", conn)
    # print(tweets_df.head())
    # print(df.head())
    # for column, row in df.iterrows():
    #     operator_name = row['operator_name']
    #     overall_sent = row['overall_sent']
    #     sql_cursor.execute("""INSERT INTO Weeks VALUES (?,?,?,?,?)""",
    #                        (month,
    #                         year,
    #                         region,
    #                         operator_name,
    #                         overall_sent))
    #     conn.commit()
    # result_list = list(sql_cursor.fetchall())
    # print(result_list)
    # for x in results:
    #     print(x)


