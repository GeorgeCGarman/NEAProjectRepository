import folium
import time
from geopy.geocoders import Nominatim
from geotext import GeoText
import geograpy
import dataset
db = dataset.connect('sqlite:///twitter.db')
m = folium.Map(
    location=[45.372, -121.6972],
    zoom_start=1,
    tiles='Stamen Terrain'
)

tooltip = 'Click me!'

count = 0
max = 500
for tweet in db['tweets']:
    # print(tweet['user_location'])
    # places = geograpy.get_place_context(text=tweet['user_location'])
    location = tweet['user_location']
    if location is not None:
        places = GeoText(location)
        # print('countries:', places.countries)
        # print('cities:', places.cities)
        if places.cities and places.countries:
            city = places.cities[0]
            country = places.countries[0]
            geolocator = Nominatim(user_agent='map_test')
            time.sleep(1)
            loc = geolocator.geocode(str(city + ',' + country))
            print(loc)
            popup = 'text:', tweet['text'], 'city:', city
            polarity = tweet['polarity']
            if polarity < 0:
                color = 'red'
            elif polarity > 0:
                color = 'green'
            else:
                color = 'blue'
            folium.Marker([loc.latitude, loc.longitude], popup=popup, tooltip=tooltip, icon=folium.Icon(icon='fab fa-twitter',prefix='fa', color=color)).add_to(m)
    else:
        print('None')
    count+=1
    print(count)
    if count > max:
        break
m.save('map.html')

