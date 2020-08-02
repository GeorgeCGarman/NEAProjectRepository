import tweepy
import sqlite3
import json
connection = sqlite3.connect("NetworkDB.db")
cursor=connection.cursor()

auth = tweepy.AppAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq", "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
api = tweepy.API(auth)
# for tweet in tweepy.Cursor(api.search, q='vodafone OR "tesco mobile"', lang='en', geocode='51.752022,-1.257677,100000km', result_type='recent').items(10):
#    print(tweet.text)

class APIManager:
    def __init__(self):
        auth = tweepy.AppAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
        api = tweepy.API(auth)
    def searchTwitter(self):
        public_tweets = tweepy.Cursor(api.search,q='vodafone signal OR "tesco mobile" signal OR o2 signal OR "ee" signal OR threeuk signal OR virgin signal',truncated='true',lang='en').items()
        return public_tweets

class DatabaseManager:
    def addTweets(self, tweets):
        count = 1
        cursor.execute("""DELETE FROM Tweet""")
        connection.commit()
        for tweet in tweets:
            print(tweet.text)
            cursor.execute("""INSERT INTO Tweet 
                VALUES(?,?,?,?)""", (count,tweet.text,tweet.coordinates,'vodafone'))
            connection.commit()
            count += 1

myAPIManager = APIManager()
myDatabaseManager = DatabaseManager()
myDatabaseManager.addTweets(myAPIManager.searchTwitter())
connection.close()
