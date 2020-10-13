import tweepy
import sqlite3
import math
import json
from textblob import TextBlob
import map
import time

conn = sqlite3.connect('twitterDB.db')
sql_cursor = conn.cursor()

auth = tweepy.OAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq",
                      "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
api = tweepy.API(auth)


def get_data():  # Loop over each county (region) and request for tweets within it
    all_regions = sql_cursor.execute("""SELECT ctyua17nm, lat, long, st_areashape
                                FROM Counties_and_Unitary_Authorities__December_2017__Boundaries_UK""").fetchall()
                                # Get the relevant information from every county in the database
    rate_limit_reached = False
    count = 0
    while count < len(all_regions):
        county = all_regions[count]
        region, lat, long, area = county[0], county[1], county[2], county[3]
        public_tweets = get_tweets_for_region(region, lat, long, area)
        while not rate_limit_reached:
            try:
                tweet = public_tweets.next()
                add_to_table(tweet, region)
            except tweepy.TweepError:
                rate_limit_reached = True
            except StopIteration:
                break

        if rate_limit_reached:
            print("Error, max requests exceeded")
            time.sleep(60 * 15)
            continue
        else:
            count += 1
        print(count)


def get_tweets_for_region(region, lat, long, area):
    print(region)
    radius = math.sqrt(area / math.pi) / 1000
    geocode = str(str(lat) + "," + str(long) + "," + str(radius) + "km")
    public_tweets = tweepy.Cursor(api.search,
                                  q='vodafone -filter:retweets',
                                  geocode=geocode,
                                  count=100, tweet_mode='extended').items()
    return public_tweets


def add_to_table(tweet, region):
    json_str = json.dumps(tweet._json)
    parsed = json.loads(json_str)
    # tweet attributes
    id_str = parsed['id']
    # if  parsed['full_text'] is not None:
    text = parsed['full_text']
    sentiment = TextBlob(text).sentiment
    polarity = sentiment.polarity
    subjectivity = sentiment.subjectivity
    created_at = parsed['created_at']
    retweet_count = parsed['retweet_count']
    favorite_count = parsed['favorite_count']  # nullable
    user_id = parsed['user']['id_str']

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
        sql_cursor.execute("""INSERT INTO tweets VALUES (?,?,?,?,?,?,?,?,?)""",
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
        sql_cursor.execute("""INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)""",
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


get_data()
conn.close()
map.make_map()
