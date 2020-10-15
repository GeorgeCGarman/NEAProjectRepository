import json
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import random
import dataset
db = dataset.connect("sqlite:///twitterDB.db")

uk_regions = json.load(open("ukcounties.json", 'r'))
d = {'id': [], 'tweets': [], 'averageSent': [], 'count': []}

def make_map():
    for feature in uk_regions['features']:
        feature['id'] = feature['properties']['NAME_2']

        d['id'].append(feature['id'])
        table = db['tweets']
        results = table.find(region=feature['id'])
        totalSent = 0
        count = 0
        fulltext = ''
        for result in results:
            totalSent += result['polarity']
            count += 1
            text = result['text']
            fulltext += "\n"+text

        d['tweets'].append(fulltext)
        d['count'].append(count)
        if count > 0:
            averageSent = totalSent/count
            d['averageSent'].append(averageSent)
        else:
            d['averageSent'].append(0.0)

    df = pd.DataFrame(d)

    fig = go.Figure(go.Choroplethmapbox(geojson=uk_regions, locations=df['id'],
                               z=df['averageSent'], zmin=-1, zmax=1,
                               colorscale= "viridis", #["red", "white", "green"], #[(0,"red"), (0.4,"lightred"), (0.5,"yellow"), (0.6,"lightgreen"), (1,"green")],
                               marker_line_width=0.1,
                               text=df['count']))

    fig.update_layout(mapbox_style="carto-darkmatter",
                    mapbox_zoom=4, mapbox_center = {"lat": 55.3781, "lon": -3.4360})
    fig.show()

