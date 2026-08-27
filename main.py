import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
# DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
connection = psycopg2.connect( host=os.getenv('host'),
user = os.getenv('user'),
port = os.getenv('port'),
database = os.getenv('database'),
password = os.getenv('password')
)
if connection:
       print("Conectou com sucesso")
else:
       print("nao deu certo")