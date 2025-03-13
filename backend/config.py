import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Gemini Configuration
GOOGLE_API_KEY = "AIzaSyC5zEinq8gaFKWr33_Mjusxbm-fyYS0YZA"
LLM_MODEL = "gemini-1.5-flash"  # Gemini model name

# Neon DB Configuration
NEON_DB_USER = "rkhealth_owner"
NEON_DB_PASSWORD =  "npg_BtX0zy9ihTvl"
NEON_DB_HOST = "ep-still-mud-a179txrz-pooler.ap-southeast-1.aws.neon.tech"
NEON_DB_PORT = "5432"
NEON_DB_NAME ="rkhealth"

# SQLite Configuration
SQLITE_DB_PATH = 'extracted_data.db'

# Flask Configuration
DEBUG = True
HOST = '0.0.0.0'
PORT = 8000