import tweepy
import sqlite3
import json
from textblob import TextBlob
from datetime import datetime, date, time, timedelta
import pandas as pd
from sqlalchemy import create_engine

# sqlite_connection = engine.connect()

TWITTER_APP_KEY = "2iOmsupNqQn32DJ1EJuo1sYQz"  # Authentication codes for Twitter API
TWITTER_APP_SECRET = "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw"

TWITTER_ACCOUNTS = ["@VodafoneUK", "@ThreeUK", "@O2", "@EE"]
COLOURS = {"@VodafoneUK": "#d62728",
           "@ThreeUK": "#000000",
           "@O2": "#1f77b4",
           "@EE": "#bcbd22"}
DB = 'twitterDB.db'
# COLOURS = ["#E60000", "#000000", "blue", "yellow"]
# COLOURS = ["red", "black", "lightblue", "yellow"]

auth = tweepy.AppAuthHandler(TWITTER_APP_KEY, TWITTER_APP_SECRET)  # Authentication for use of Twitter API.
# Keys provided when creating a Twitter Application
# as a Twitter Developer
api = tweepy.API(auth)


def get_data():  # Loop over each county (region) and request for tweets within it
    conn = sqlite3.connect(DB)  # Connect to sqlite3 database
    cur = conn.cursor()
    all_regions = cur.execute("""SELECT name, latitude, longitude, radius
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
            except sqlite3.IntegrityError:  # If we find a repeated tweet, then we don't need to look at the rest of
                # the tweets, as they are returned in chronological order so all the others will already be in the
                # database
                break

        if rate_limit_reached:
            print("Error, max requests exceeded")
            break  # Stop if rate limit reached
        else:
            count += 1
        print(count)
    conn.close()


def get_tweets_for_region(lat, long, radius):  # Makes the request to the API for tweets within a specific area
    geocode = str(str(lat) + "," + str(long) + "," + str(radius) + "km")
    query = " OR ".join(TWITTER_ACCOUNTS) + " -filter:retweets"
    public_tweets = tweepy.Cursor(api.search,
                                  q=query,
                                  geocode=geocode,
                                  tweet_mode='extended').items()
    # searches for tweets with the keyword vodafone in their text,
    # filtering out retweets, and in extended mode, which returns the full tweet text
    return public_tweets


def add_to_table(tweet, region):  # Parse the tweet JSON and insert it into the sqlite3 table. The region parameter
    # specifies the region the tweet came from
    conn = sqlite3.connect(DB)  # Connect to sqlite3 database
    cur = conn.cursor()
    json_str = json.dumps(tweet._json)
    parsed = json.loads(json_str)

    # tweet attributes
    tweet_id = parsed['id']
    text = parsed['full_text']
    sentiment = TextBlob(text).sentiment
    polarity = round(sentiment.polarity, 3)  # how positive or negative the tweet is
    subjectivity = round(sentiment.subjectivity,
                         3)  # subjective sentences generally refer to personal opinion, emotion or
    # judgment whereas objective refers to factual information
    created_at = datetime.strptime(parsed['created_at'], '%a %b %d %H:%M:%S +0000 %Y')  # Date tweet was created
    retweet_count = parsed['retweet_count']  # How many retweets
    favorite_count = parsed['favorite_count']  # How many favourites
    if parsed['place'] is not None:
        place = parsed['place']  # place of the tweet e.g. London UK
        full_name = place['full_name']
        place_type = place['place_type']
        country = place['country']
        cur.execute("""INSERT INTO Place VALUES (?,?,?,?)""",
                    (tweet_id,
                     full_name,
                     place_type,
                     country))
        conn.commit()

    if parsed['coordinates'] is not None:
        coords = str(parsed['coordinates']['coordinates'])  # coordinates of the tweet (if given)
        cur.execute("""INSERT INTO Coordinates VALUES (?,?)""",
                    (tweet_id,
                     coords))
        conn.commit()

    # user attributes
    user = parsed['user']
    user_id = user['id_str']
    user_name = user['name']
    user_location = user['location']  # Location user gives in their profile. E.g. 'London, UK'
    user_description = user['description']  # Twitter bio
    user_verified = user['verified']  # Is the user verified?
    user_followers_count = user['followers_count']
    user_friends_count = user['friends_count']
    user_favourites_count = user['favourites_count']
    user_statuses_count = user['statuses_count']  # How many tweets user has made
    user_created_at = user['created_at']  # Date when account was created

    for operator_name in TWITTER_ACCOUNTS:
        if operator_name in text:
            cur.execute("""INSERT INTO TweetOperator VALUES (?,?)""",
                        (tweet_id, operator_name))
            conn.commit()

    cur.execute("""INSERT INTO Tweets VALUES (?,?,?,?,?,?,?,?,?)""",
                (tweet_id,
                 text,
                 polarity,
                 subjectivity,
                 created_at,
                 retweet_count,
                 favorite_count,
                 user_id,
                 region))
    conn.commit()

    cur.execute("""INSERT INTO Users VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (user_id,
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
    conn.close()


def condense_db():
    def date_to_week(my_date):
        return str(my_date.year) + '-' + str(my_date.month) + '-' + str(
            (my_date.day - 1) // 7)  # returns the week of the
        # tweet

    conn = sqlite3.connect(DB)  # Connect to sqlite3 database
    df = pd.read_sql_query("""SELECT region_name, created_at, operator_name, polarity
                              FROM Tweets, TweetOperator
                              WHERE Tweets.tweet_id=TweetOperator.tweet_id""", conn)  # Get the region, date,
    # network operator and sentiment polarity of all the tweets in the database and put them in a Pandas dataframe

    max_date_in_db = datetime.strptime(max(df['created_at']), '%Y-%m-%d %H:%M:%S')  # The date and time of the most
    # recent tweet
    days_to_subtract = 6 + int(
        max_date_in_db.day % 7)  # subtract 1 week from this and round it down to the previous week
    max_date = max_date_in_db - timedelta(days=days_to_subtract,
                                          hours=max_date_in_db.hour,
                                          minutes=max_date_in_db.minute,
                                          seconds=max_date_in_db.second)  # max_date represents the date of the first
    # day of the week that is at least 1 week before the most recent tweet.

    print(max_date_in_db)
    print(days_to_subtract)
    print(max_date)

    df['created_at'] = pd.to_datetime(df['created_at'])  # make the created_at field datetime objects
    df = df[df['created_at'] < max_date]  # Select the dates we want to condense
    if df.empty:
        return  # If there aren't any tweets to condense, return
    df['week'] = df['created_at'].apply(date_to_week)  # Create the new column 'week'
    grouped = df.groupby(['region_name', 'week', 'operator_name'])
    print('grouped:', grouped.head())
    agged = grouped \
        .agg(tweet_count=('polarity', 'count'), overall_sent=('polarity', 'sum')) \
        .reset_index()  # Creates columns for the sum of the tweets and the sum of the polarities
    max_overall_sent = max(map(abs, agged['overall_sent']))  # overall_sent calculated in the usual way
    agged['overall_sent'] = agged['overall_sent'] / max_overall_sent
    engine = create_engine('sqlite:///{}'.format(DB), echo=True)
    agged.to_sql('Weeks', engine, if_exists='append', index=False)  # append the database to the Weeks table
    cur = conn.cursor()
    cur.execute("""DELETE FROM Tweets
                   WHERE created_at < '{}'""".format(max_date))  # remove the Tweets that have been condensed.
    conn.commit()
    conn.close()

    # DELETE FROM Tweets
    # WHERE created_at < '2021-04-21 00:00:00'
