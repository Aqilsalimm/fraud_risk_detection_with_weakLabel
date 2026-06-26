import requests
import os

api_key = os.getenv("GEMINI_API_KEY")
headers = {"Content-Type": "application/json"}
payload = {
    "contents": [{
        "parts": [{
            "text": "Hello, write a 1 sentence greeting in Indonesian."
        }]
    }]
}

models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.5-flash"]

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    print(f"Testing {model}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"-> {model} Status:", response.status_code)
        if response.status_code == 200:
            print("-> Success!")
            print(response.json()["candidates"][0]["content"]["parts"][0]["text"])
            break
        else:
            print(f"-> Response: {response.text[:300]}")
    except Exception as e:
        print("-> Error:", e)
