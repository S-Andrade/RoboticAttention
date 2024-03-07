# -*- coding: utf-8 -*-
import json
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt


with open('graph.json', encoding="utf8") as f:
    data = json.load(f)

nodes = []

for d in data:
    nodes.append(d['node_1'])
    nodes.append(d['node_2'])

nodes = list( dict.fromkeys(nodes) )

print(nodes)


G = nx.MultiGraph()

## Add nodes to the graph
for node in nodes:
    G.add_node(str(node), label=str(node))

## Add edges to the graph
for d in data:
    G.add_edge(
        str(d["node_1"]),
        str(d["node_2"]),
        title=d["edge"],
        #label=d["edge"]
    )



g =Network(height=900, width=1500, notebook=True, directed=True)
g.toggle_hide_edges_on_drag(True)
g.from_nx(G)
#g.show_buttons()
g.set_edge_smooth('dynamic')
g.show("graph.html")