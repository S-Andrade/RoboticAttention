from langchain_community.vectorstores import Neo4jVector
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_community.llms import VertexAI
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_secret_key.json'

vector_store_extra_text = Neo4jVector.from_existing_index(
    #embedding=VertexAIEmbeddings(),
    url='bolt://localhost:7687',
    username="neo4j",
    password="handmadev2",
    database="neo4j",
    #index_name=VECTOR_INDEX_NAME,
    #text_node_property=VECTOR_SOURCE_PROPERTY,
    #retrieval_query=retrieval_query_window, 
)

# Create a retriever from the vector store
retriever = vector_store_extra_text.as_retriever()

# Create a chatbot Question & Answer chain from the retriever
chain = RetrievalQAWithSourcesChain.from_chain_type(
    VertexAI(temperature=0), 
    chain_type="stuff", 
    retriever=retriever
)

chain("Onde o que o miguel fez na manhã de sabado?")