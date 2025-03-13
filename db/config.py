import os
from dotenv import load_dotenv
from llama_index.llms.groq import Groq

# Load environment variables
load_dotenv()

# Neon DB connection parameters
NEON_DB_USER = os.getenv("NEON_DB_USER")
NEON_DB_PASSWORD = os.getenv("NEON_DB_PASSWORD")
NEON_DB_HOST = os.getenv("NEON_DB_HOST")
NEON_DB_PORT = os.getenv("NEON_DB_PORT")
NEON_DB_NAME = os.getenv("NEON_DB_NAME")

# SQLite configuration
SQLITE_DB_FILE = "chat_sessions.db"

# Groq API key for LLM
API_KEY = os.getenv("API_KEY")
llm = Groq(model="llama3-70b-8192", api_key=API_KEY)