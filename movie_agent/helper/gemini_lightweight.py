import os
import requests


class GeminiLightClient:
    def __init__(self, model="gemini-2.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateText?key={self.api_key}"
        self.session = requests.Session()

    def generate(self, prompt, temperature=1):
        body = {
            "prompt": {"text": prompt},
            "temperature": temperature,
            "maxOutputTokens": 512
        }

        res = self.session.post(self.url, json=body, timeout=8)
        data = res.json()

        try:
            return data["candidates"][0]["output"]
        except:
            return "{}"
