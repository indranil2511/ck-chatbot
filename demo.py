import os
from dotenv import load_dotenv
load_dotenv()
CONNECTION_STRING = os.getenv('CONNECTION_STRING')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
connection_string = "postgresql+psycopg2://postgres:priya@localhost:5434/postgres"
collection_name = 'CK_Articles'  
print(COLLECTION_NAME or collection_name)
print(CONNECTION_STRING or connection_string)