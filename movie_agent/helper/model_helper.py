from movie_agent.helper.gemini_lightweight import GeminiLightClient

class AIModelProvider:
    def __init__(self):
        self.gemini = GeminiLightClient()

    def get_ai_response(self, messages):
        prompt = "\n".join(m["content"] for m in messages)
        prompt += "\n\nRespond ONLY with valid JSON matching the schema. No explanations."

        text = self.gemini.generate(prompt)

        return text, True
