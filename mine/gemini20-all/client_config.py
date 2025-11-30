# client_config.py

import os
from google import genai
from google.genai.types import HttpOptions
from dotenv import load_dotenv

# Load environment variables (ensure this is called before client is created)
load_dotenv()

# The genai.Client object
# This code runs only ONCE when the module is first imported.
client = genai.Client(
    http_options=HttpOptions(api_version="v1")
)

MODEL = "gemini-2.5-flash-live-api" 
TRANSCRIPTION_MODEL = "gemini-1.5-flash"
# MODEL = "gemini-2.0-flash-exp"
# TRANSCRIPTION_MODEL = "gemini-1.5-flash-8b"
