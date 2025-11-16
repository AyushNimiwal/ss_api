import os
import requests

class GeminiLightClient:
    def __init__(self, model="gemini-2.5-flash-lite"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        self.session = requests.Session()

    def generate(self, prompt, temperature=0.9):
        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 512
            }
        }

        res = self.session.post(self.url, json=body, timeout=12)
        data = res.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("PARSE ERR:", e)
            return "{}"
