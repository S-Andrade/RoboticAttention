
from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import os
from neo4j import unit_of_work

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'handmadev2'))
session = driver.session()

def executeQuery(query):
    
    result = session.run(query)
    
    return result

def queryNodes(node_label, l):

    query = "CREATE ( p:" + node_label + " {"
    for k , v in l.items():
        if k != "_uid":
            query += k +": '" + v +"', "
        
    query = query[:-2]
    query += "})"

    return query


def queryRelationships(re, n1, nn1, n2, nn2):
    return  "MATCH (a:" + nn1 +" {nome:'" + n1 +"'}), (b:" + nn2 +" {nome:'" + n2 +"'}) \nCREATE (a)-[:" + re + "]->(b)" 

def find(nodes, id):
    nl = ""
    n = ""
    for node_label, lista in nodes.items():
        for l in lista:
            if l["_uid"] == id:
                return l["nome"] , node_label
    

def main():
    executeQuery("MATCH (n) DETACH DELETE n")

    with open("time.json", encoding='utf-8') as json_data:
        data = json.load(json_data)

    nodes = data['nodes']

    relationships = data["relationships"]


    for node_label, lista in nodes.items():
        for l in lista:
            query = queryNodes(node_label,l)
            print(query)
            executeQuery(query)

    for re, lista in relationships.items():
            for l in lista:
                n1, nn1 = find(nodes, l["_from_uid"])
                n2, nn2 = find(nodes, l["_to_uid"])
                query = queryRelationships(re, n1, nn1, n2, nn2)
                executeQuery(query)

main()