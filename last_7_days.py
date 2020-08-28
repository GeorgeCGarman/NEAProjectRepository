import tweepy
from textblob import TextBlob
import dataset
import time
from geopy.geocoders import Nominatim
db = dataset.connect('sqlite:///last_7_days.db')
#import tree_last_7_days
# import dataset
# db = dataset.connect('sqlite:///last_7_days.db')
db['tweets'].delete()

auth = tweepy.OAuthHandler("2iOmsupNqQn32DJ1EJuo1sYQz", "0kDqCC3yRqbLEQtIThXe0nwoHS9UXhoLht7R0c2VHiSt2szHPw")
auth.set_access_token("863763963946860544-Xkas3C3b7TW8oEKNWQEOPmryiEGA3Iq", "PTGcHBqO4qFxiMD2iPFUBY1wHyCG5Tm0aTshCyhejQk2i")
api = tweepy.API(auth)

geocode='55.3781,-3.4360,500km'
public_tweets = tweepy.Cursor(api.search, q='vodafone -filter:retweets',geocode=geocode).items()
for tweet in public_tweets:
    description = tweet.user.description
    loc = tweet.user.location
    coords = str(tweet.coordinates)
    if tweet.place is not None:
        place = tweet.place
        place_name = place.full_name
        #print('place:', place)
        bounding_box = str(tweet.place.bounding_box.coordinates)

        #print('coords:', coords)
    else:
        place = None
        place_name = None
        bounding_box = None
    text = tweet.text
    name = tweet.user.screen_name
    user_created = tweet.user.created_at
    followers = tweet.user.followers_count
    id_str = tweet.id_str
    created = tweet.created_at
    retweets = tweet.retweet_count
    bg_color = tweet.user.profile_background_color
    blob = TextBlob(text)
    sent = blob.sentiment
    table = db["tweets"]
    table.insert(dict(
        user_description=description,
        user_location=loc,
        place=place_name,
        place_name=place_name,
        bounding_box=bounding_box,
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
        subjectivity=sent.subjectivity, ))
    # if loc is not None:
    #     geolocator = Nominatim(user_agent='map_test')
    #     geoInfo = geolocator.geocode(loc, language='en')
    #     time.sleep(1)
    #     if geoInfo is not None:
    #         print('geoInfo.address:', geoInfo.address)
    #         # print('geoInfo:',geoInfo.raw)
    #         address = geoInfo.address.replace(" ", "").split(',')
    #         print(address)
    #         print(geoInfo.raw)
    #         tree_last_7_days.add(id_str, address)