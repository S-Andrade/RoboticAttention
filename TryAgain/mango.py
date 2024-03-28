import threading
import time

# -*- coding: utf-8 -*-
import json
import sys
import re
from threading import Thread
import random
import queue
import re
import sys
import time
from google.cloud import speech
import pyaudio
import json
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'google_secret_key.json'
from playsound import playsound
import pyttsx3
from io import BytesIO
from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import os
from neo4j import unit_of_work
from openai import OpenAI
import re
from itertools import chain, combinations
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
from IPython.display import Markdown, display
from random import randint
from ElmoV2API import ElmoV2API



# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms



RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
  
def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=load_api_key(),
)
os.environ["OPENAI_API_KEY"] =load_api_key()

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'handmadev2'))
session = driver.session()

neo4j_vector = Neo4jVectorStore('neo4j', 'handmadev2', 'bolt://localhost:7687', 1536)

documents = SimpleDirectoryReader("doc").load_data()

storage_context = StorageContext.from_defaults(vector_store=neo4j_vector)
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)

query_engine = index.as_query_engine(
    include_text=True,
    response_mode="tree_summarize",
    embedding_mode="hybrid",
    similarity_top_k=5,
)

robot_ip = "192.168.0.102"
robot = ElmoV2API(robot_ip, debug=True)
robot.enable_behavior(name="look_around", control = False)
robot.set_pan(0)
robot.set_tilt(-8)
robot.set_pan_torque(True)

with open('time.json', encoding="utf-8") as f:
    data = json.load(f)


def get_current_time() -> int:
    return int(round(time.time() * 1000))

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

def getPromptTwo(query, vector_result, graph_result):
    return f"""You are a helpful question-answering agent. Your task is to analyze 
        and synthesize information from two sources: the top result from a similarity search 
        (unstructured information) and relevant data from a graph database (structured information). 
        Given the user's query: {query}, provide a meaningful and efficient answer based 
        on the insights derived from the following data:

        Unstructured information: {vector_result}. 
        Structured information: {graph_result}.
        A tua resposta deve de ser sumarizada e deves extrair a informação mais importante e escreve-la numa versão simples, curta, simpatica e informal. 
        Deves de ser o mais curto possivel! Usa no maximo 10 palavras!
        Têm em consideração todos os dados que te são fornecidos!
        Pensa duas vezes antes de dar uma resposta!
        Deves de só responder ao que te foi perguntado, não des informação a mais!
        Só podes usar portugues europeu!
        Se a resposta não tem sentido ou não conseguires responder podes dizer que não sabes!
        """

def getPromptNew(newpista,pistas):
    return f"""
        Tu és um analisador de Knowledge graphs. O teu trabalho é perceber se a informação de um texto está contida na lista de outputs de uma query de neo4j.
        Deves de procurar a informação que está no texto em cada elemto da lista.
        Deves perceber se toda a informação do texto está contida no output do neo4j.
        Deves de responder só com sim ou não. 
        O teu output deve de ser só uma palavra, sim ou não!
        texto: '''{newpista}'''
        lista de outputs do neo4j: ***{pistas}***
    """

def getPromptQuery(frase, nodes):
    return f"""
        Tu és um especialista em Knowledge graphs. E consequentemente és especialista em neo4j.
        Vais receber uma frase entre ``` e o teu trabalho é criares uma query para adicionar a informaçção que está nessa frase num base de dados neo4j.
        Deves de criar um query que adiciona a informação a uma base de dados com os nós que estão entre ***.
        Só deves de usar os nós que são referidos na frase.
        Se precisares de usar um nó que não existe deves de o criar na tua query!
        O teu output deve de ser só a query.
        Só podes usar português europeu!
        frase: ```{frase}```
        nós: ***{nodes}***
    """

def getPromptPergunta(evento):
    return f"""
        Tu és um especialista a perguntar perguntas.
        Vai receber um evento entre ***, que está descrito atraves dos 5W1H.
        O teu trabalho é perceber que elementos do 5W1H falta e escrever uma pergunta que falte.
        evento: ***{evento}*** 
    """

def getPromptComentario(evento):
    return f"""
        Tu és um experiente comentador.
        Vai receber um evento entre ***. 
        O teu trabalho é fazer um comentario sobre o evento.
        O comentario deve de ter no maximo 10 palavras.
        Não deves de adicionar informação, diz só que está no evento!
        Por favor escreve o teu comentario com a melhor ortografia que consigas!
        evento: ***{evento}*** 
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message.content.strip()

def Input(event, data, nodes):
    
    previous = []
    messages = []
    historico = {'user': [], 'robot': []}

    while True:

        message = input("User: ")
        robot.set_pan(-40)
        robot.set_screen("thinking.png")

        historico['user'] += [message]
        m1 = [{"role": "user", "content": getPromptQuestion(message)}]
        question = chatGPT(m1)   
        
        keys = [n for n in nodes if re.search(n, message, re.IGNORECASE)]
        if re.search("Sr.Gaia", message, re.IGNORECASE) or re.search("Sr. Gaia", message, re.IGNORECASE) or re.search("Senhor Gaia", message, re.IGNORECASE):
            if "Casa do Sr.Gaia" not in keys:
                keys += ["Roberto"]

        print(keys)

        t = []
        
        if len(keys) == 1:
            t = [ [n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ keys[0] +"'})-[r]-(b)return a, r, b").data()]
            previous = []

        if len(keys) > 1:
            previous = []
            lista = list(combinations(keys, 2))
            for l in lista:
                t += [[n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ l[0] +"'})-[r]-(b {nome: '"+ l[1] +"'})return a, r, b").data()]
            if len(t) <= 2:
                for k in keys:
                    t += [ [n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ k +"'})-[r]-(b)return a, r, b").data()]


        #print(question)
        if question == "True":
            vector_result = query_engine.query(message)
            print(vector_result)
            messages += [{"role": "user", "content": getPromptTwo(message, vector_result, t)}]
            response = chatGPT(messages)

        if question == "False":
            m1 = [{"role": "user", "content": getPromptNew(message,t)}]
            tem = chatGPT(m1)
            #print(tem)
            if tem[-1] == ".":
                tem = tem[:-1]
            if tem.upper() == "SIM":
                response = "Sim, eu também tenho essa informação"
            if tem.upper() == "NÃO":
                m2 = [{"role": "user", "content": getPromptQuery(message,data["nodes"])}]
                newquery = chatGPT(m2)
                print(newquery)
                executeQuery(newquery)
                response = "Não sabia isso!"

        #print(">" + response)
        
        
        r = response 

        if response != "Não sabia isso!" and response != "Sim, eu também tenho essa informação":
            if any(x in response for x in historico['robot']):   
                r = "Como eu já disse, " + response
            if any(x in response for x in historico['user']):
                r = "Como já disseste, " + response
            
            historico['robot'] += [response]
        print("--" + r)
        robot.set_screen("normal.png")
        #time.sleep(2)
        robot.speak(r,"pt")
        robot.set_pan(0)
        """engine.say(r)
        engine.iterate()
        while engine.isBusy(): # wait until finished talking
            time.sleep(0.1)         
        engine.endLoop()"""


def askquestion(event, enable,):
    """engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    voice = None
    for v in voices:
        if "Cristiano22" in v.id:
            voice = v.id
    engine.setProperty('voice', voice)
    engine.startLoop(False)"""
    if enable:
        event.set()
        #robot.set_pan(-40)
        #robot.set_tilt(-8)
        a = executeQuery("MATCH (n:Evento) WITH n, rand() AS r ORDER BY r RETURN n LIMIT 1").data()
        number = randint(1, 100)
        if number <= 70:
            messages = [{"role": "user", "content": getPromptComentario(a)}]
            r = chatGPT(messages)
        else:
            messages = [{"role": "user", "content": getPromptPergunta(a)}]
            r = chatGPT(messages)
        #robot.speak(r,"pt")
        """engine.say(question)
        engine.iterate()
        while engine.isBusy(): # wait until finished talking
            time.sleep(0.1)         
        engine.endLoop()"""
    else:
        event.clear()
        

def main(): 
    

    with open('time.json', encoding="utf8") as f:
        data = json.load(f)
    
    nodes = [n["n.nome"] for n in executeQuery("MATCH (n) RETURN n.nome").data() if n["n.nome"] != None]


    event = threading.Event()
    a = threading.Thread(target=Input, args=(event, data, nodes, )).start()

    stime = time.time()
    while True:
        if time.time() - stime > 60:
            stime = time.time()
            
            b = threading.Thread(target=askquestion, args=(event, True, )).start()
            time.sleep(2)
            c = threading.Thread(target=askquestion, args=(event, False, )).start()
    a.start()
    a.join()



if __name__ == "__main__":
    main()




        

