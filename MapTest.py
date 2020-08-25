import folium
import time
from geopy.geocoders import Nominatim
from geotext import GeoText
import geograpy
import dataset
db = dataset.connect('sqlite:///twitter.db')

def addMarker(tweet):
    if tweet['user_location'] is not None:
        print(tweet['text'])
        user_location = tweet['user_location']
        places = geograpy.get_place_context(text=user_location)
        geolocator = Nominatim(user_agent='map_test')
        loc = geolocator.geocode(user_location)
        if loc is not None:
            popup = 'text: %s' % (tweet['text'])
            polarity = tweet['polarity']
            if polarity < 0:
                color = 'red'
            elif polarity > 0:
                color = 'green'
            else:
                color = 'blue'
            tooltip = 'Click me!'
            folium.Marker([loc.latitude, loc.longitude], popup=popup, tooltip=tooltip,
                            icon=folium.Icon(icon='fab fa-twitter', prefix='fa', color=color)).add_to(m)
            m.save('map.html')
            print('yes')


# count = 1
# for tweet in db['tweets']:
#     print(count)
#     # print(tweet['user_location'])
#     # places = geograpy.get_place_context(text=tweet['user_location'])
#     location = tweet['user_location']
#     print('location:',location)
#     if location is not None:
#         geolocator = Nominatim(user_agent='map_test')
#         loc = geolocator.geocode(location)
#         if loc is not None:
#             popup = 'text:',tweet['text']
#             polarity = tweet['polarity']
#             if polarity < 0:
#                 color = 'red'
#             elif polarity > 0:
#                 color = 'green'
#             else:
#                 color = 'blue'
#             print('loc:',loc)
#             folium.Marker([loc.latitude, loc.longitude], popup=popup, tooltip=tooltip,
#                             icon=folium.Icon(icon='fab fa-twitter', prefix='fa', color=color)).add_to(m)
#             time.sleep(1)
#     else:
#         print('None')
#     print('')
#     count+=1


