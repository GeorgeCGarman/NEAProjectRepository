import tweepy
import sqlite3
import math
import json
from textblob import TextBlob
import map

conn = sqlite3.connect('twitterDB.db')
sql_cursor = conn.cursor()

auth = tweepy.OAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq", "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
api = tweepy.API(auth)

def get_data():
    counties = sql_cursor.execute("""SELECT ctyua17nm, lat, long, st_areashape
                                FROM Counties_and_Unitary_Authorities__December_2017__Boundaries_UK""").fetchall()
    count = 0
    for county in reversed(counties):
        name, lat, long, area = county[0], county[1], county[2], county[3]
        print(name)
        radius = math.sqrt(area/math.pi)/1000
        geocode = str(str(lat)+","+str(long)+","+str(radius)+"km")
        try:
            public_tweets = tweepy.Cursor(api.search,
                                      q='vodafone -filter:retweets',
                                      geocode=geocode,
                                      count=100).items()
        except:
            print("Error, max requests exceeded")
            break

        for tweet in public_tweets:
            json_str = json.dumps(tweet._json)
            parsed = json.loads(json_str)

            # tweet attributes
            id_str = parsed['id']
            text = parsed['text']
            sentiment = TextBlob(text).sentiment
            polarity = sentiment.polarity
            subjectivity = sentiment.subjectivity
            created_at = parsed['created_at']
            retweet_count = parsed['retweet_count']
            favorite_count = parsed['favorite_count'] # nullable
            user_id = parsed['user']['id_str']
            region = name

            # user attributes
            user = parsed['user']
            user_id_str = user['id_str']
            user_name = user['name']
            user_location = user['location']
            user_description = user['description']
            user_verified = user['verified']
            user_followers_count = user['followers_count']
            user_friends_count = user['friends_count']
            user_favourites_count = user['favourites_count']
            user_statuses_count = user['statuses_count']
            user_created_at = user['created_at']

            try:
                sql_cursor.execute("""INSERT INTO tweets
                                  (id_str,
                                   text,
                                   polarity,
                                   subjectivity,
                                   created_at,
                                   retweet_count,
                                   favorite_count,
                                   user_id,
                                   region)
                                  VALUES (?,?,?,?,?,?,?,?,?)""",
                                   (id_str,
                                    text,
                                    polarity,
                                    subjectivity,
                                    created_at,
                                    retweet_count,
                                    favorite_count,
                                    user_id,
                                    region))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
            try:
                sql_cursor.execute("""INSERT INTO users
                                          (user_id_str,
                                           user_name,
                                           user_location,
                                           user_description,
                                           user_verified,
                                           user_followers_count,
                                           user_friends_count,
                                           user_favourites_count,
                                           user_statuses_count,
                                           user_created_at)
                                          VALUES (?,?,?,?,?,?,?,?,?,?)""",
                               (user_id_str,
                                user_name,
                                user_location,
                                user_description,
                                user_verified,
                                user_followers_count,
                                user_friends_count,
                                user_favourites_count,
                                user_statuses_count,
                                user_created_at))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
        count += 1
        print(count)
conn.close()
map.make_map()





