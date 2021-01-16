import pandas as pd
import sqlite3
import json
import dataset

con = sqlite3.connect("twitterDB.db")
con.row_factory = lambda cursor, row: row[0]
cur = con.cursor()

uk_regions = json.load(open("ukcounties.json", 'r'))

regions = cur.execute("SELECT name FROM regions")
#con.close()
# db = dataset.connect("sqlite:///twitterDB.db")
con.row_factory = lambda cursor, row: row
regionsdf = pd.read_sql_query("SELECT name FROM regions", con)
#print(regionsdf.head())

mylist = []
for feature in uk_regions['features']:
    name = feature['properties']['NAME_2']
    i = regionsdf[regionsdf['name'] == name]
    # print(i)
    if i.empty:
        print(name)
    mylist.append(name)
for i in range(3):
    print('-')

count = 0
for x in regions:
    if x in mylist:
        pass
    else:
        print(x)
        count +=1
print(count)

