import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")