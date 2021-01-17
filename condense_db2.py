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
for region in all_regions:
    min_date =
    df = pd.read_sql_query("""SELECT AVG(polarity) as avg_polarity, operator_name
                                    FROM Tweets, TweetOperator
                                    WHERE Tweets.tweet_id=TweetOperator.tweet_id 
                                          AND Tweets.region_name="{}"
                                          AND Tweets.created_at BETWEEN
                                    GROUP BY TweetOperator.operator_name""".format(region), conn)
    for column, row in df.iterrows():
        operator_name = row['operator_name']
        avg_polarity = row['avg_polarity']
        sql_cursor.execute("""INSERT INTO Weeks VALUES (?,?,?,?,?)""",
                           (month,
                            year,
                            region,
                            operator_name,
                            avg_polarity))
        conn.commit()
    # result_list = list(sql_cursor.fetchall())
    # print(result_list)
    # for x in results:
    #     print(x)


