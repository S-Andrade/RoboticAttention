import os
import json
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.query_engine import KnowledgeGraphQueryEngine
from llama_index.core import StorageContext
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import KnowledgeGraphIndex

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

os.environ["OPENAI_API_KEY"]=load_api_key()

llm = OpenAI(temperature=0, model="gpt-3.5-turbo")
Settings.llm = llm
Settings.chunk_size = 512

graph_store = Neo4jGraphStore(
            username="neo4j",
            password="handmadev2",
            url='bolt://localhost:7687',
            database="neo4j",
)


storage_context = StorageContext.from_defaults(graph_store=graph_store)
"""
index = KnowledgeGraphIndex(
        #nodes=nodes,
        storage_context=storage_context,
        max_triplets_per_chunk=2,
        include_embeddings=True,
        llm=llm
    )
query_engine = index.as_query_engine(include_text=False, response_mode="tree_summarize") 
query_engine.query("Onde o que o miguel fez na manhã de sabado?")  """ 


print(llm.predict("migitas"))

query_engine = KnowledgeGraphQueryEngine(
    storage_context=storage_context,
    llm=llm,
    verbose=True,
)

response = query_engine.query(
    "Onde o que o miguel fez na manhã de sabado?",
)
print(response)