import tweepy
import sqlite3
import math
import json
from textblob import TextBlob
import map
import dash_app
import time
import dataset
from sqlalchemy.sql import text
from datetime import datetime

TWITTER_APP_KEY = "2iOmsupNqQn32DJ1EJuo1sYQz"  # Authentication codes for Twitter API
TWITTER_APP_SECRET = "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw"

auth = tweepy.AppAuthHandler(TWITTER_APP_KEY, TWITTER_APP_SECRET)  # Authentication for use of Twitter API.
# Keys provided when creating a Twitter Application
# as a Twitter Developer
api = tweepy.API(auth)

conn = sqlite3.connect('twitterDB.db')  # Connect to sqlite3 database
sql_cursor = conn.cursor()


def get_data():  # Loop over each county (region) and request for tweets within it
    all_regions = sql_cursor.execute("""SELECT name, latitude, longitude, radius
                                FROM Regions""").fetchall()

    # Get the relevant information from every county (named as 'regions') in the database
    rate_limit_reached = False
    count = 0
    while count < len(all_regions):  # Loop over each county
        region = all_regions[count]
        region_name, lat, long, radius = region[0], region[1], region[2], region[3]
        print(region_name)
        public_tweets = get_tweets_for_region(lat, long, radius)
        while not rate_limit_reached:  # Loop over each tweet received and insert it into the database
            try:
                tweet = public_tweets.next()
                add_to_table(tweet, region_name)
            except tweepy.TweepError:  # If the rate limit has been reached (450 requests made), raise an exception
                rate_limit_reached = True
            except StopIteration:  # If we have finished iterating over all the tweets in public_tweets
                break

        if rate_limit_reached:
            print("Error, max requests exceeded")
            break  # Stop if rate limit reached
        else:
            count += 1
        print(count)


def get_tweets_for_region(lat, long, radius):  # Makes the request to the API for tweets within a specific area
    geocode = str(str(lat) + "," + str(long) + "," + str(radius) + "km")
    public_tweets = tweepy.Cursor(api.search,
                                  q='vodafone -filter:retweets',
                                  geocode=geocode,
                                  tweet_mode='extended').items()
    # searches for tweets with the keyword vodafone in their text,
    # filtering out retweets, and in extended mode, which returns the full tweet text
    return public_tweets


def add_to_table(tweet, region):  # Parse the tweet JSON and insert it into the sqlite3 table. The region parameter
    # specifies the region the tweet came from
    json_str = json.dumps(tweet._json)
    parsed = json.loads(json_str)

    # tweet attributes
    id_str = parsed['id']
    text = parsed['full_text']
    sentiment = TextBlob(text).sentiment
    polarity = sentiment.polarity  # how positive or negative the tweet is
    subjectivity = sentiment.subjectivity  # subjective sentences generally refer to personal opinion, emotion or
    # judgment whereas objective refers to factual information
    created_at = datetime.strptime(parsed['created_at'],'%a %b %d %H:%M:%S +0000 %Y') # Date tweet was created
    retweet_count = parsed['retweet_count']  # How many retweets
    favorite_count = parsed['favorite_count']  # How many favourites
    user_id = parsed['user']['id_str']  # Link tweet to its user

    # user attributes
    user = parsed['user']
    user_id_str = user['id_str']
    user_name = user['name']
    user_location = user['location']  # Location user gives in their profile. E.g. 'London, UK'
    user_description = user['description']  # Twitter bio
    user_verified = user['verified']  # Is the user verified?
    user_followers_count = user['followers_count']
    user_friends_count = user['friends_count']
    user_favourites_count = user['favourites_count']
    user_statuses_count = user['statuses_count']  # How many tweets user has made
    user_created_at = user['created_at']  # Date when account was created

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
    except sqlite3.IntegrityError:  # if the tweet is already in the database, discard it.
        print('Error, repeated tweet')
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
        print('Error, repeated user')
        pass

get_data()
dash_app.run_dash_app()
conn.close()
