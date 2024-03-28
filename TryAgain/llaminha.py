import json
import os
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import KnowledgeGraphRAGRetriever
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.core import ServiceContext 
from llama_index.core import KnowledgeGraphIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.core.indices.vector_store.retrievers.retriever import VectorIndexRetriever
from llama_index.core.indices.knowledge_graph import KGTableRetriever
from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import QueryBundle
from llama_index.core.query_engine import KnowledgeGraphQueryEngine

# import NodeWithScore
from llama_index.core.schema import NodeWithScore

# Retrievers
from llama_index.core.retrievers import (
    BaseRetriever,
    VectorIndexRetriever,
    KeywordTableSimpleRetriever,
)

from typing import List

class CustomRetriever(BaseRetriever):
    """Custom retriever that performs both semantic search and hybrid search."""

    def __init__(
        self,
        vector_retriever: VectorIndexRetriever,
        keyword_retriever: KeywordTableSimpleRetriever,
        mode: str = "AND",
    ) -> None:
        """Init params."""

        self._vector_retriever = vector_retriever
        self._keyword_retriever = keyword_retriever
        if mode not in ("AND", "OR"):
            raise ValueError("Invalid mode.")
        self._mode = mode
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""

        vector_nodes = self._vector_retriever.retrieve(query_bundle)
        keyword_nodes = self._keyword_retriever.retrieve(query_bundle)

        vector_ids = {n.node.node_id for n in vector_nodes}
        keyword_ids = {n.node.node_id for n in keyword_nodes}

        combined_dict = {n.node.node_id: n for n in vector_nodes}
        combined_dict.update({n.node.node_id: n for n in keyword_nodes})

        if self._mode == "AND":
            retrieve_ids = vector_ids.intersection(keyword_ids)
        else:
            retrieve_ids = vector_ids.union(keyword_ids)

        retrieve_nodes = [combined_dict[rid] for rid in retrieve_ids]
        return retrieve_nodes


def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

os.environ["OPENAI_API_KEY"]=load_api_key()


neo4j_graph_store = Neo4jGraphStore(
    username="neo4j",
    password="hiddenprofiles",
    url='bolt://localhost:7687',
    database="neo4j",
)

neo4j_storage_context = StorageContext.from_defaults(
    graph_store=neo4j_graph_store
)

# define LLM
llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")
service_context = ServiceContext.from_defaults(llm=llm)

docs = "doc"

"""neo4j_index = KnowledgeGraphIndex.from_documents(
    documents=docs,
    storage_context=neo4j_storage_context,
    max_triplets_per_chunk=10,
    service_context=service_context,
    include_embeddings=True,
)

# create node parser to parse nodes from document
node_parser = SentenceSplitter(chunk_size=512)

# use transforms directly
nodes = node_parser(docs)
print(f"loaded nodes with {len(nodes)} nodes")

# based on the nodes and service_context, create index
vector_index = VectorStoreIndex(
    nodes=nodes, service_context=service_context
)"""


query_engine_type = "KG_QE"
"""
if query_engine_type == "KG_KEYWORD":
    # KG keyword-based entity retrieval
    query_engine = neo4j_index.as_query_engine(
        # setting to false uses the raw triplets instead of adding the text from the corresponding nodes
        include_text=False,
        retriever_mode="keyword",
        response_mode="tree_summarize",
    )

elif query_engine_type == "KG_HYBRID":
    # KG hybrid entity retrieval
    query_engine = neo4j_index.as_query_engine(
        include_text=True,
        response_mode="tree_summarize",
        embedding_mode="hybrid",
        similarity_top_k=3,
        explore_global_knowledge=True,
    )

elif query_engine_type == "RAW_VECTOR":
    # Raw vector index retrieval
    query_engine = vector_index.as_query_engine()

elif query_engine_type == "RAW_VECTOR_KG_COMBO":
    
    # create neo4j custom retriever
    neo4j_vector_retriever = VectorIndexRetriever(index=vector_index)
    neo4j_kg_retriever = KGTableRetriever(
        index=neo4j_index, retriever_mode="keyword", include_text=False
    )
    neo4j_custom_retriever = CustomRetriever(
        neo4j_vector_retriever, neo4j_kg_retriever
    )

    # create neo4j response synthesizer
    neo4j_response_synthesizer = get_response_synthesizer(
        service_context=service_context,
        response_mode="tree_summarize",
    )

    # Custom combo query engine
    query_engine = RetrieverQueryEngine(
        retriever=neo4j_custom_retriever,
        response_synthesizer=neo4j_response_synthesizer,
    )
"""
if query_engine_type == "KG_QE":
    # using KnowledgeGraphQueryEngine

    query_engine = KnowledgeGraphQueryEngine(
        storage_context=neo4j_storage_context,
        service_context=service_context,
        llm=llm,
        verbose=True,
    )

elif query_engine_type == "KG_RAG_RETRIEVER":
    # using KnowledgeGraphRAGRetriever

    neo4j_graph_rag_retriever = KnowledgeGraphRAGRetriever(
        storage_context=neo4j_storage_context,
        service_context=service_context,
        llm=llm,
        verbose=True,
    )

    query_engine = RetrieverQueryEngine.from_args(
        neo4j_graph_rag_retriever, service_context=service_context
    )

"""else:
    # KG vector-based entity retrieval
    query_engine = neo4j_index.as_query_engine()"""

r = query_engine.query("Quem é a Maria?",)
print(r)