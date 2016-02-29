#!/usr/bin/env python

import dill
from model import *
from igraph import *
# import networkx as nx
# import matplotlib.pyplot as plt
# import pydot
# import nx_pygraphviz

model_in_fp = open('restaurant_model_20docs', 'r')
M = dill.load(model_in_fp)

connections = map(lambda k: [k[0], k[1], M.PMI[k]], filter(lambda key: M.PMI[key] != 0, M.PMI.keys()))

nodes = []
edges = []
# edgenumbers = []
weights = []
for connection in connections:
	nodeA = connection[0]
	nodeB = connection[1]
	edge_weight = connection[2]
	indA = len(nodes)
	nodes.append(nodeA)
	indB = len(nodes)
	nodes.append(nodeB)
	edges.append((nodeA, nodeB))
	# edgenumbers.append((indA, indB))
	weights.append(edge_weight)
nodes = list(set(nodes))
edgenumbers = [(nodes.index(edge[0]), nodes.index(edge[1])) for edge in edges]
weights = map(lambda w: w*2, weights)

g = Graph(directed=True)

g.add_vertices(len(nodes))
g.add_edges(edgenumbers)

g.vs['name'] = nodes
# g.vs["label"] = g.vs["name"]

layout = g.layout('fr')
visual_style = {}
visual_style["vertex_size"] = 10
visual_style['vertex_label_dist'] = 3
# visual_style["vertex_shape"] = 'hidden'
visual_style["bbox"] = (1000, 1000)
visual_style["vertex_color"] = 'white'
visual_style["layout"] = layout
visual_style["margin"] = 100
visual_style["vertex_label"] = g.vs["name"]
# visual_style["edge_width"] = weights

plot(g, **visual_style)

print(g)

# nodelist = list(set(nodes))

# G=nx.DiGraph()

# for edge in connections:
# 	G.add_edge(edge[0],edge[1],weight=edge[2])

# edgelist=[(u,v,d) for (u,v,d) in G.edges(data=True)]

# pos=nx.spring_layout(G) # positions for all nodes

# # nodes
# nx.draw_networkx_nodes(G,pos,node_size=2000, node_color='w')

# # edges
# nx.draw_networkx_edges(G,pos,edgelist=edgelist,
# 	width=[d['weight']*10 for (u,v,d) in edgelist])

# # labels
# nx.draw_networkx_labels(G,pos,font_size=8,font_family='sans-serif')

# write_dot(G, 'restaurant_20docs.dot')