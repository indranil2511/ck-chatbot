from langchain.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
open_ai_key = os.getenv('OPEN_AI_KEY')
load_dotenv()





def main():
    embeddings = OpenAIEmbeddings(openai_api_key=open_ai_key)

    CONNECTION_STRING = "postgresql+psycopg2://postgres:priya@localhost:5434/postgres"
    COLLECTION_NAME = 'knowledge_articles'  

    db = PGVector(embedding_function=embeddings,
                                 collection_name=COLLECTION_NAME,
                                 connection_string=CONNECTION_STRING)
   
   
    query = "Duet AI for Google Workspace"
   
    similar = db.similarity_search_with_score(query, k=1)
    for doc in similar:
     print(doc, end="\n\n")
 
  
    
    
   
    



if __name__ == "__main__":
    main()