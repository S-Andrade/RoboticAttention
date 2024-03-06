# -*- coding: utf-8 -*-
import json
import openai 
import networkx as nx
from pyvis.network import Network

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

api_key = load_api_key()
openai.api_key = api_key

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]



file = open(".\pistas.txt", encoding="utf8")
lines =  file.readlines()
pistas = ""
for line in lines:
    if "*" not in line:
        pistas+=line

file.close()


prompt_2 = f"""
You are a network graph maker who extracts the relations between terms from a given context.
You are provided with a context chunk (delimited by ```).
Your task is to extract the ontology of terms mentioned in the given context.
These terms are Bruno, sábado, assasinato, Miguel, Ricardo, Campo de Golf, MAuto, Café, Empregada Café, Sr.Gaia, pé-de-cabra, Eduardo, Sara, Oficina Gaia, clientes, carteira, posto, Maria.
Think about how these terms can have one on one relation with other terms. Terms that are mentioned in the same sentence or the same paragraph are typically related to each other. Terms can be related to many other terms.
Format your output as a json. Each element contains a pair of terms and the relation between them. With  node_1, node_2 and edge as keys.
Interviews: ```{pistas}```
"""

prompt_3 = f"""
You are a network graph maker who extracts the relations between terms from a given context.
You are provided with a context chunk (delimited by ```).
Your task is to extract the ontology of terms mentioned in the given context.
These terms are Bruno, sábado, assasinato, Miguel, Ricardo, Campo de Golf, MAuto, Café, Empregada Café, Sr.Gaia, pé-de-cabra, Eduardo, Sara, Oficina Gaia, clientes, carteira, posto, Maria. Do not add more terms!
Knowing this list of terms, for each sentence you must find the two terms that are mentioned there. Then think about the relationship that the sentence suggests that these two terms have.
Format your output as a json. Each element contains a pair of terms and the relation between them. With  node_1, node_2 and edge as keys.
Interviews: ```{pistas}```
"""

prompt_4 = f"""
You are a network graph maker who extracts the relations between terms from a given context.
You are provided with a context chunk (delimited by ```).
Your task is to extract the ontology of terms mentioned in the given context.
These terms are Bruno, sábado, assasinato, Miguel, Ricardo, Campo de Golf, MAuto, Café, Empregada Café, Sr.Gaia, pé-de-cabra, Eduardo, Sara, Oficina Gaia, clientes, carteira, posto, Maria. Do not add more terms!
Knowing this list of terms, for each sentence you must find the two terms that are mentioned there. 
Format your output as a json. Each element contains a pair of terms and the sentence . With  node_1, node_2 and edge as keys
Interviews: ```{pistas}```
"""


response = get_completion(prompt_4)

with open("hp.json", "w") as outfile:
    outfile.write(response)


with open('hp.json') as f:
    data = json.load(f)

nodes = []

for d in data[list(data.keys())[0]]:
    nodes.append(d['node_1'])
    nodes.append(d['node_2'])

nodes = list( dict.fromkeys(nodes) )


G = nx.MultiGraph()

## Add nodes to the graph
for node in nodes:
    G.add_node(str(node), label=str(node))

## Add edges to the graph
for d in data[list(data.keys())[0]]:
    G.add_edge(
        str(d["node_1"]),
        str(d["node_2"]),
        title=d["edge"],
        label=d["edge"]
    )



g =Network(height=900, width=1500, notebook=True, directed=True)
g.toggle_hide_edges_on_drag(True)
g.from_nx(G)
g.show_buttons()
g.set_edge_smooth('dynamic')
g.show("graphChatGPT.html")

