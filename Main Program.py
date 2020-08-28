import tweepy
from textblob import TextBlob
from geopy.geocoders import Nominatim
import dataset
import json
import folium
import geograpy
import time
import tree
db = dataset.connect('sqlite:///twitter.db')

# import dataset
# db = dataset.connect('sqlite:///twitter.db')
# db['tweets'].delete()

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        try:
            if status.retweeted_status:
                return
        except:
            pass

        if not status.truncated:
            text = status.text
        else:
            text = status.extended_tweet['full_text']
        description = status.user.description
        loc = status.user.location
        coords = status.coordinates
        name = status.user.screen_name
        user_created = status.user.created_at
        followers = status.user.followers_count
        id_str = status.id_str
        created = status.created_at
        retweets = status.retweet_count
        bg_color = status.user.profile_background_color
        blob = TextBlob(text)
        sent = blob.sentiment
        if coords is not None:
            coords = json.dumps(coords)
            #print(coords)

        table = db["tweets"]
        row = dict(
            user_description=description,
            user_location=loc,
            coordinates=coords,
            text=text,
            user_name=name,
            user_created=user_created,
            user_followers=followers,
            id_str=id_str,
            created=created,
            retweet_count=retweets,
            user_bg_color=bg_color,
            polarity=sent.polarity,
            subjectivity=sent.subjectivity, )
        table.insert(row)
        table = db["locations"]
        print()
        print('text:',text)
        print('place:',status.place)
        print('user_location:',loc)
        if loc is not None:
            geolocator = Nominatim(user_agent='map_test')
            geoInfo = geolocator.geocode(loc, language='en')
            time.sleep(1)
            if geoInfo is not None:
                print('geoInfo.address:',geoInfo.address)
                #print('geoInfo:',geoInfo.raw)
                address = geoInfo.address.replace(" ","").split(',')
                print(address)
                print(geoInfo.raw)
                tree.add(id_str,address)



    def on_error(self, status_code):
        if status_code == 420:
            return False


auth = tweepy.OAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq", "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
api = tweepy.API(auth)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, tweet_mode='extended')
myStream.filter(track=['vodafone'])
#myStream.filter(locations=[-7.57216793459, 49.959999905, 1.68153079591, 58.6350001085])