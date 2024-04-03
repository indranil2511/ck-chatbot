from openai import Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from langchain.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
open_ai_key = os.getenv('OPEN_AI_KEY')

txt = []
client = Client(api_key=open_ai_key)
# Read file
loader = TextLoader('./Cloudkaptan.txt', encoding='utf-8')
documents = loader.load()
# Load the spaCy model
def get_embedding(text, model="text-embedding-3-small"):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size= 1000, chunk_overlap=200)
    texts = text_splitter.split_documents(text)
    embeddings = OpenAIEmbeddings(openai_api_key=open_ai_key)
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
    host=os.environ.get("PGVECTOR_HOST", "localhost"),
    port=int(os.environ.get("PGVECTOR_PORT", "5434")),
    database=os.environ.get("PGVECTOR_DATABASE", "postgres"),
    user=os.environ.get("PGVECTOR_USER", "postgres"),
    password=os.environ.get("PGVECTOR_PASSWORD", "priya"),
    )
    collection_name = 'CK_Articles'  

    db = PGVector(embedding_function=embeddings,
                                 collection_name= collection_name,
                                 connection_string= CONNECTION_STRING )
    db = PGVector.from_documents(
        embedding=embeddings,
        documents=texts,
        collection_name=collection_name,
        connection_string=CONNECTION_STRING,
    
    )

get_embedding(documents,"text-embedding-3-small")