from openai import OpenAI
import json

class AIModelProvider():

    def __init__(self):
        self.client = OpenAI()

    
    def get_ai_response(self, model, messages, temperature=0):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature
            )
            content = response.choices[0].message.content
            return content, True
        except Exception as e:
            return {"error": str(e)}, False