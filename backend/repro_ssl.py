import httpx
import os

print("--- Testing httpx Connectivity ---")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")

targets = [
    ("Google (Gemini)", "https://generativelanguage.googleapis.com"),
    ("OpenAI", "https://api.openai.com"),
    ("DeepSeek", "https://api.deepseek.com")
]

for name, url in targets:
    try:
        resp = httpx.get(url, timeout=5)
        print(f"[{name}] Status: {resp.status_code}")
    except Exception as e:
        print(f"[{name}] Error: {type(e).__name__}: {e}")
