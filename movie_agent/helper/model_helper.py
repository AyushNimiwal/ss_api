from movie_agent.helper.gemini_lightweight import GeminiLightClient

class AIModelProvider:
    def __init__(self):
        self.gemini = GeminiLightClient()

    def get_ai_response(self, messages):
        prompt = ""
        for m in messages:
            role = "User" if m["role"] == "user" else "System"
            prompt += f"{role}: {m['content']}\n"

        prompt += "\nReturn ONLY pure JSON."

        text = self.gemini.generate(prompt)

        return text, True
