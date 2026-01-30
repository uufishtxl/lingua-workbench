import requests
import os

proxies = {
    "http": os.environ.get("HTTP_PROXY"),
    "https": os.environ.get("HTTPS_PROXY")
}

print(f"Testing connectivity with proxies: {proxies}")

targets = [
    ("Google", "https://www.google.com"),
    ("OpenAI", "https://api.openai.com"),
    ("DeepSeek", "https://api.deepseek.com")
]

for name, url in targets:
    try:
        response = requests.get(url, proxies=proxies, timeout=5)
        print(f"[{name}] Status: {response.status_code}")
    except Exception as e:
        print(f"[{name}] Failed: {e}")
