import json
import os
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.core import ServiceContext 
from llama_index.core import Settings
from llama_index.core.query_engine import KnowledgeGraphQueryEngine

from llama_index.core.settings import Settings
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.legacy.query_engine import KnowledgeGraphQueryEngine


def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

os.environ["OPENAI_API_KEY"]=load_api_key()

neo4j_graph_store = Neo4jGraphStore(
            username="neo4j",
            password="handmadev2",
            url='bolt://localhost:7687',
            database="neo4j",
)

neo4j_storage_context = StorageContext.from_defaults(
            graph_store=neo4j_graph_store
)

#Settings.llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")

"""neo4j_graph_rag_retriever = KnowledgeGraphRAGRetriever(
    storage_context=neo4j_storage_context,
    verbose=True,
)

query_engine = RetrieverQueryEngine.from_args(
    neo4j_graph_rag_retriever
)
"""
"""query_engine = KnowledgeGraphQueryEngine(
        storage_context=neo4j_storage_context,
        verbose=True,
    )"""


"""llm = HuggingFaceLLM(model_name="mistralai/Mistral-7B-Instruct-v0.2", tokenizer_name="mistralai/Mistral-7B-Instruct-v0.2", device_map="auto", generate_kwargs={"temperature": 0.001, "do_sample":True}, 
    max_new_tokens=1024)

embed_model = LangchainEmbedding(
  HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
)
"""

llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")

Settings.llm = llm

cypher_query_engine = KnowledgeGraphQueryEngine(
    storage_context=neo4j_storage_context,
    llm=llm,
    verbose=True,
)

r = cypher_query_engine.query("Quem o Roberto?")
print(r.source_nodes)

#display(Markdown(f"<b>{response}</b>"))