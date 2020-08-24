import sqlite3
import tweepy
import math

connection = sqlite3.connect('NetworkDB.db')
cursor = connection.cursor()

auth = tweepy.AppAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
api = tweepy.API(auth) #wait_on_rate_limit=True)

class DatabaseManager:
    def __init__(self):
        self.count = 0
        cursor.execute("""DELETE FROM Tweet""")
        connection.commit()

    def add_tweets(self, tweets, locationID):
        for tweet in tweets:
            print(tweet.text)
            try:
                cursor.execute("""INSERT INTO Tweet 
                    VALUES(?,?,?,?)""", (tweet.id, tweet.text, locationID, 'vodafone'))
            except sqlite3.IntegrityError:
                print('error, repeated tweet')
            connection.commit()
            self.count += 1

locations = cursor.execute("""SELECT Latitude,Longitude,Area,LocationID
                            FROM Local_Authority_Districts__December_2017__Boundaries_in_Great_Britain

                            """)

locationList = []

for location in locations.fetchall():
    locationList.append([location[0], location[1], location[2], location[3]])

# for location in locationList:
#     lat = location[0]
#     long = location[1]
#     area = location[2]
#     print(lat, long, area)


myDatabaseManager = DatabaseManager()
count = 0
for location in locationList[50:100]:
    lat = location[0]
    long = location[1]
    area = location[2]
    print(lat, long, area)
    mylocationID = location[3]
    radius = math.sqrt(location[2]/(math.pi))/1000
    myGeocode = "%s,%s,%s" % (str(lat), str(long), str(radius)+'km')
    myTweets = tweepy.Cursor(api.search, q="vodafone -filter:retweets", geocode=myGeocode).items()
    myDatabaseManager.add_tweets(myTweets,mylocationID)
    count += 1
    print(count)
connection.close()