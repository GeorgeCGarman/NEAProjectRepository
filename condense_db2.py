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

df['week'] = df['created_at'].apply(week)
grouped = df.groupby(['region_name', 'week', 'operator_name'])
agged = grouped.agg(overall_sent=pd.NamedAgg(column="polarity", aggfunc=sum)).reset_index()
max_overall_sent = max(map(abs, agged['overall_sent']))
agged['overall_sent'] = agged['overall_sent'] /  max_overall_sent
print(agged)
#print(agged.loc[agged['overall_sent'] == 1])

