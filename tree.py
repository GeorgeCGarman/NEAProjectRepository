from treelib import Node, Tree
from geopy.geocoders import Nominatim
import time
import json

treefile = open('locations_tree.txt', 'r')
treeDict = json.load(treefile)
def createTreeFromDict(tree,dict,parent=None):
    print(dict)
    firstKey = list(dict.keys())[0]
    #data = list(dict.keys())[1]
    currentNode = Node(identifier=firstKey)
    print('currentNode:',currentNode)
    if firstKey == 'children':
        parent.data = dict[list(dict.keys())[1]]
        for key in dict['children']:
            createTreeFromDict(tree,key,parent)
    elif firstKey == 'data':
        parent.data = dict['data']
    else:
        if parent is not None:
            tree.add_node(currentNode, parent=parent)
            print('added:',currentNode)
        else:
            tree.add_node(currentNode)
            print('added:', currentNode)
        createTreeFromDict(tree, dict[firstKey], currentNode)
locations = Tree()
createTreeFromDict(locations,treeDict)
root = locations.root
locations.show()
def add(id,locationList):
    locationList.reverse()
    newBranch = False
    for i in range(len(locationList)):
        location = locationList[i]
        node = locations.get_node(location)
        geolocator = Nominatim(user_agent='map_test')
        geoInfo = geolocator.geocode(location)
        try:
            lat = geoInfo.raw['lat']
            long = geoInfo.raw['lon']
            print('accepted:', geoInfo.raw)
        except AttributeError:
            print('exception:',location)
            lat = None
            long = None
        time.sleep(1)
        newNode = Node(identifier=location,data=[lat,long])
        print('getnode:',locations.get_node(location))
        if node is None:
            newBranch = True
        if newBranch == True:
            if i == 0:
                locations.add_node(newNode,parent=root)
            else:
                parent = locations.get_node(locationList[i-1])
                print(i)
                print(locationList[i-1])
                print(parent)
                locations.add_node(newNode,parent)
    lastNode = locations.get_node(locationList[len(locationList)-1])
    tweetNode = Node(id,data=[lastNode.data[0],lastNode.data[1]])
    print(id,[lat,long])
    locations.add_node(tweetNode,parent=lastNode)
    locations.show()
    with open('locations_tree.txt','w') as file:
        newFile = locations.to_json(with_data=True)
        #json.dumps(newFile, file)
        file.write(newFile)
    #with open('locations_tree.txt', 'r') as file:
        #myFile = file.read()
        #print(myFile)

#geolocator = Nominatim(user_agent='tree')
#geoInfo = geolocator.geocode(loc)
#time.sleep(1)