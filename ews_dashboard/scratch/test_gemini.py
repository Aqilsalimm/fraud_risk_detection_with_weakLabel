import requests
import json

api_key = "[GCP_API_KEY]"
headers = {"Content-Type": "application/json"}
payload = {
    "contents": [{
        "parts": [{
            "text": "Hello, write a 1 sentence greeting in Indonesian."
        }]
    }]
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

print("Testing Google AI Studio endpoint with gemini-2.0-flash...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
