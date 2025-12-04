import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_gemini_models():
    print("Available Gemini Models:")
    for model in genai.list_models():
        print(model.name)

if __name__ == "__main__":
    list_gemini_models()




