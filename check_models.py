import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your API key
load_dotenv("/opt/pe-sourcing-engine/config/secrets.env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Available Models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f" - {m.name}")
