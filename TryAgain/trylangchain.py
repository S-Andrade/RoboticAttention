from langchain.chat_models import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.graphs import Neo4jGraph
import json
import os
from pypdf import PdfReader
import asyncio
import warnings
from langchain._api import LangChainDeprecationWarning
warnings.simplefilter("ignore", category=LangChainDeprecationWarning)
import json
import sagemaker
import boto3
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri
from langchain.prompts import PromptTemplate


def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

os.environ["OPENAI_API_KEY"] =load_api_key()
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)

graph = Neo4jGraph(
    url="bolt://localhost:7687", 
    username="neo4j", 
    password="handmadev2"
)

#print(graph.schema)~

CYPHER_GENERATION_TEMPLATE = """
Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)


chain_language_example = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0), graph=graph, verbose=True
)

escreve = open("respostas.txt", "a", encoding="utf-8")

with open("perguntas.txt", encoding="utf-8") as file:
    for line in file:
        escreve.write(line)
        resposta = chain_language_example.run(line)
        print(resposta)
        escreve.write(">" + resposta + "\n")


