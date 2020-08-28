from treelib import Node, Tree
from collections import defaultdict
import json
import folium
import treelib
import ast
import dataset
db = dataset.connect('sqlite:///twitter.db')

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
tree = Tree()
root = Node('Earth')
createTreeFromDict(tree,treeDict)

# newNode = Node(child[])
# tree.add_node(newNode,parent=root)
# newNode = Node(treeDict['Earth']['children'])

tree.show()


m = folium.Map(
    location=[45.372, -121.6972],
    zoom_start=1,
)
table = db['tweets']
for node in tree.all_nodes_itr():
    print(node.identifier)
    print(node.data)
    if not node.is_leaf():
        popup = ''
        totalPolarity = 0
        count = 0
        for child in tree.children(node.identifier):
            if child.is_leaf():
                if child.data is not None:
                    data = child.data
                else:
                    data = node.data
                tweet = table.find_one(id_str=child.identifier)
                if tweet is not None:
                    text = tweet['text']
                    user = tweet['user_name']
                    polarity = tweet['polarity']
                    totalPolarity += polarity
                    if count == 0:
                        popup += '<b>'+user+'</b>'+'<br>'+'<i>'+text+'</i>'
                    else:
                        popup += '<br>' + '<br>' +'<b>'+user+'</b>'+'<br>'+'<i>'+text+'</i>'
                    count += 1

        if count > 0:
            averagePolarity = totalPolarity/count
            if averagePolarity < -0.1:
                color = 'red'
            elif averagePolarity > 0.1:
                color = 'green'
            else:
                color = 'blue'
            tooltip = 'Click me!'
            if data[0] is not None:
                folium.Marker([data[0], data[1]], popup=popup, tooltip=tooltip,
                    icon=folium.Icon(icon='fab fa-twitter', prefix='fa', color=color)).add_to(m)
        if count > 1:
            print('YES')
            print('id:',node.identifier)
    # if node.is_leaf():
    #     parent = node.parent
    #     if node.data is not None:
    #         data = node.data
    #     else:
    #         data = node.parent.data
    #     tweet = table.find_one(id_str=node.identifier)
    #     if tweet is not None:
    #         popup = tweet['text']
    #         polarity = tweet['polarity']
    #         if polarity < 0:
    #             color = 'red'
    #         elif polarity > 0:
    #             color = 'green'
    #         else:
    #             color = 'blue'
    #         tooltip = 'Click me!'
    #         if data[0] is not None:
    #             folium.Marker([data[0], data[1]], popup=popup, tooltip=tooltip,
    #                         icon=folium.Icon(icon='fab fa-twitter', prefix='fa', color=color)).add_to(m)
m.save('map.html')

