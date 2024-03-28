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


driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'handmadev2'))
session = driver.session()

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=load_api_key(),
)
os.environ["OPENAI_API_KEY"] =load_api_key()

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
        Deves de escrever tudo numa frase com no maximo 10 palavras.
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
        Deves de criar um query que adiciona a informação a uma base de dados com os nos que estão entre ***.
        Só deves de usar os nós que são referidos na frase.
        Se precisares de usar um nó que não existe deves de o criar na tua query!
        O teu output deve de ser só a query.
        Só podes usar português europeu!
        frase: ```{frase}```
        nós: ***{nodes}***
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message.content.strip()

nodes = [n["n.nome"] for n in executeQuery("MATCH (n) RETURN n.nome").data() if n["n.nome"] != None]


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

with open('time.json', encoding="utf-8") as f:
    data = json.load(f)


wf = open("respostas.txt", "a", encoding="utf-8")

with open("perguntas.txt", encoding="utf-8") as fp:
    for line in fp:
        message = input("User:")
        #message = line
        #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + message)
        #wf.write(line)
        m1 = [{"role": "user", "content": getPromptQuestion(message)}]
        question = chatGPT(m1)   
        
        keys = [n for n in nodes if re.search(n, message, re.IGNORECASE)]

        if re.search("Sr.Gaia", message, re.IGNORECASE) or re.search("Sr. Gaia", message, re.IGNORECASE) or re.search("Senhor Gaia", message, re.IGNORECASE):
            keys += ["Roberto"]

        print(keys)

        t = []
        
        if len(keys) == 1:
            t = [ [n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ keys[0] +"'})-[r]-(b)return a, r, b").data()]

        if len(keys) > 1:
            lista = list(combinations(keys, 2))
            for l in lista:
                t += [[n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ l[0] +"'})-[r]-(b {nome: '"+ l[1] +"'})return a, r, b").data()]
            if t == []:
                for k in keys:
                    t += [ [n["a"], n["r"], n["b"]] for n in executeQuery("MATCH (a {nome: '"+ k +"'})-[r]-(b)return a, r, b").data()]
        
        print(question)
        if question == "True":
            print(t)
            vector_result = query_engine.query(message)
            messages = [{"role": "user", "content": getPromptTwo(message, vector_result, t)}]
            response = chatGPT(messages)

        if question == "False":
            messages = [{"role": "user", "content": getPromptNew(message,t)}]
            tem = chatGPT(messages)
            print(tem)
            if tem[-1] == ".":
                tem = tem[:-1]
            if tem.upper() == "SIM":
                response = "Sim, eu também tenho essa informação"
            if tem.upper() == "NÃO":
                messages = [{"role": "user", "content": getPromptQuery(message,data["nodes"])}]
                newquery = chatGPT(messages)
                print(newquery)
                executeQuery(newquery)
                response = "Não sabia isso!"

        print(">" + response)
        #wf.write(">"+ response + "\n")