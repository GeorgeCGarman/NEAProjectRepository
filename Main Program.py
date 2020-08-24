import json
import tweepy
import sqlite3
from nltk.sentiment.util import demo_liu_hu_lexicon
#import matplotlib

connection = sqlite3.connect("NetworkDB.db")
cursor = connection.cursor()

# auth = tweepy.AppAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
# auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq", "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
# api = tweepy.API(auth)
# for tweet in tweepy.Cursor(api.search, q='vodafone OR "tesco mobile"', lang='en', geocode='51.752022,-1.257677,100000km', result_type='recent').items(10):
#    print(tweet.text)

class APIManager:
    def __init__(self):
        self.__auth = tweepy.AppAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
        self.__api = tweepy.API(self.__auth, wait_on_rate_limit=True)
    def searchTwitter(self):
        public_tweets = tweepy.Cursor(self.__api.search,q='vodafone -filter:retweets',geocode='55.3781,-3.4360,500km',truncated='true').items()
        #print(public_tweets)
        return public_tweets

class DatabaseManager:
    def addTweets(self, tweets):
        count = 1
        cursor.execute("""DELETE FROM Tweet""")
        connection.commit()
        for tweet in tweets:
            #print(tweet.text)
            #if tweet.user.location != None:
                #print(tweet.user.location)
            #else:
                #print('error')
            cursor.execute("""INSERT INTO Tweet 
                VALUES(?,?,?,?)""", (count,tweet.text,tweet.coordinates,'vodafone'))
            connection.commit()
            count += 1

class SentimentAnalyser:
    def getSentiment(self, sentence):
        demo_liu_hu_lexicon(sentence)

myAPIManager = APIManager()
myDatabaseManager = DatabaseManager()
tweets = myAPIManager.searchTwitter()
tweetList = []
for tweet in tweets:
    # try:
    #     print(tweet.place.country)
    # except:
    #     try:
    #         print(tweet.user.location)
    #     except:
    #         print('none')
    try:
        if tweet.place != None:
            print(tweet.place)
        else:
            if tweet.user.location != None:
                print(tweet.user.location)
            else:
                print('None')
    except:
        print(tweet)
    # try:
    #     if tweet.place.country == 'United Kingdom':
    #         print(tweet.place)
    # except:
    #     try:
    #         print(tweet.user.location)
    #     except:
    #     #     print('none')
    #         pass

    # try:
    #     print(tweet)
    #     print(tweet.place.country)
    #     if tweet.place.country == 'United Kingdom':
    #         tweetList.append([tweet.text,tweet.place.full_name])
    # except:
    #     pass


#print(tweetList)
#myDatabaseManager.addTweets(tweets)
#tweetTextList = []
# for tweet in tweets:
#     tweetTextList.append(tweet.text)
# mySentimentAnalyser = SentimentAnalyser()
# for tweet in tweetTextList:
#     print(tweet)
#     mySentimentAnalyser.getSentiment(tweet)
#     print('')

connection.close()
