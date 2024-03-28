from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import os
from neo4j import unit_of_work
import openai
import re
from itertools import chain, combinations

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'handmade'))
session = driver.session()

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

api_key = load_api_key()
openai.api_key = api_key

def executeQuery(query):
    return session.run(query)

def getPromptQuestion(string):
    return f"""
    Tu és um analizador de texto. O teu trabalho é perceber se uma string é uma pergunta ou não.
    Deves de dar a tua responta em boolean. True se for uma pergunta. False se não for uma pergunta.
    String: ```{string}```
    """

def getPrompt(pistas):
    return f"""
        Tu és um elemento de uma equipa de investigação criminal. 
        O teu objetivo é relacionar as varias pistas enquanto falas com outros investigadores. Sendo que não deves resolver o caso. 
        Entre ``` estão as pistas que deves relacionar.
        És um cominador natural e consegues explicar qualquer tipo de informação de uma forma simples e rapida.
        Lembra-te que deves usar português europeu. Deves de usar um tom simpatico e informal.
        A tua resposta deve de ser sumarizada e deves extrair a informação mais importante e escreve-la numa versão simples, curta, simpatica e informal. 
        Deves de escrever tudo numa frase com no maximo 10 palavras.
        Deves de só responder ao que te foi perguntado, não des informação a mais!
        Só podes usar portugues europeu!
        Pistas: ```{pistas}```
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

nodes = [n["n.nome"] for n in executeQuery("MATCH (n) RETURN n.nome").data() if n["n.nome"] != None]


while True:
    message = input("User : ") 
       
    #m1 = [{"role": "user", "content": getPromptQuestion(message)}]
    #question = chatGPT(m1)   

    keys = [n for n in nodes if re.search(n, message, re.IGNORECASE)]
    
    if len(keys) == 1:
        t = [n["r.frase"] for n in executeQuery("MATCH (a {nome: '"+ keys[0] +"'})-[r]-()return r.frase").data()] 

    if len(keys) > 1:
        t = []
        lista = list(combinations(keys, 2))
        for l in lista:
            t += [n["r.frase"] for n in executeQuery("MATCH (a {nome: '"+ l[0] +"'})-[r]-(b {nome: '"+ l[1] +"'})return r.frase").data()]

    text = " ".join(str(x) for x in t)
    #print(text)

    messages = [{"role": "user", "content": getPrompt(text)},
                        {"role": "user", "content": message}]
    response = chatGPT(messages)

    print(response)
