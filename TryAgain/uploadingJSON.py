from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import os
from neo4j import unit_of_work

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'handmade'))
session = driver.session()

def executeQuery(query):
    
    result = session.run(query)
    
    return result

def queryNodes(node_label, l):
    query = ""
    if node_label == "Pessoa":
        if not l.get('profissao'):
            query += "CREATE ( p:" + node_label + " {nome : '" + l.get('nome') + "', sobrename : '" + l.get('sobrenome') + "'} )"
        else:
            query += "CREATE ( p:" + node_label + " {nome : '" + l.get('nome') + "', sobrename : '" + l.get('sobrenome') + "', profissão : '" + str(l.get('profissao')) + "'} )"
    
    if node_label == "Evento" or node_label == "Negocio" or node_label == "Objeto":
        query += "CREATE (q:" + node_label + " {nome : '" + l.get('nome') + "'}) "

    return query


def queryRelationships(re, n1, nn1, n2, nn2, frase):
    return  "MATCH (a:" + nn1 +" {nome:'" + n1 +"'}), (b:" + nn2 +" {nome:'" + n2 +"'}) \nCREATE (a)-[:" + re + " {frase: '" + frase +"'}]->(b)" 

def find(nodes, id):
    for node_label, lista in nodes.items():
        for l in lista:
            if l["_uid"] == id:
                return l["nome"], node_label

def main():
    with open("queries.json", encoding='utf-8') as json_data:
        data = json.load(json_data)

    nodes = data['nodes']

    relationships = data["relationships"]


    for node_label, lista in nodes.items():
        for l in lista:
            query = queryNodes(node_label,l)
            executeQuery(query)

    for re, lista in relationships.items():
            for l in lista:
                n1, nn1 = find(nodes, l["_from_uid"])
                n2, nn2 = find(nodes, l["_to_uid"])
                frase = l["frase"]
                query = queryRelationships(re, n1, nn1, n2, nn2, frase)
                executeQuery(query)

main()