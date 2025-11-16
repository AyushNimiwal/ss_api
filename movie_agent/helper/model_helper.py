import os
import google.generativeai as genai

class AIModelProvider:

    def __init__(self, model="gemini-2.5-flash", temperature=0):
        # Configure API key
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Create Gemini model
        self.client = genai.GenerativeModel(
            model,
            generation_config={"temperature": temperature}
        )

    def get_ai_response(self, messages):
        try:
            # Convert messages to a simple prompt
            prompt = ""
            for m in messages:
                role = m["role"].capitalize()
                prompt += f"{role}: {m['content']}\n\n"

            prompt += "Return ONLY valid JSON. No text outside JSON."

            # Call Gemini
            response = self.client.generate_content(prompt)

            text = response.text.strip()

            # Clean JSON wrappers if model sends markdown
            if "```" in text:
                text = text.replace("```json", "").replace("```", "").strip()

            return text, True

        except Exception as e:
            return {"error": str(e)}, False
