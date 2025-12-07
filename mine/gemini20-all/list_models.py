import google.generativeai as genai
import os
from dotenv import load_dotenv
from client_config import client

def list_gemini_models():
    # Check what models supports what
    for m in client.models.list():
        print(f"Model Name: {m.name}, Supported methods: {m.supported_actions}")

if __name__ == "__main__":
    list_gemini_models()




