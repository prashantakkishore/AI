# client_config.py

import os
from google import genai
from dotenv import load_dotenv

# Load environment variables (ensure this is called before client is created)
load_dotenv()

# The genai.Client object
# This code runs only ONCE when the module is first imported.
client = genai.Client()

# MODEL = "gemini-1.5-flash" 
# TRANSCRIPTION_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL_NAME="models/text-embedding-004"
MODEL = "gemini-2.5-flash-native-audio-preview-09-2025"
CHROMA_RAG_MODEL="gemini-2.5-flash"
TRANSCRIPTION_MODEL = "gemini-2.5-flash"
