from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
import os
from neo4j import unit_of_work
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
from IPython.display import Markdown, display

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

os.environ["OPENAI_API_KEY"] =load_api_key()

neo4j_vector = Neo4jVectorStore('neo4j', 'bdpistas', 'bolt://localhost:7687', 1536)

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

with open("perguntas.txt", encoding="utf-8") as fp:
    for line in fp:
        line.replace("\n", "")
        print(line)
        response = query_engine.query(line)
        print(response)
#display(Markdown(f"<b>{response}</b>"))



