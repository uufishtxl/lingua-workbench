import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("📋 List of available embedding models:")
for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(f"  👉 {m.name}")