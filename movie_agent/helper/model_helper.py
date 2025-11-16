import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class AIModelProvider:

    def __init__(self, model="gemini-2.5-pro", temperature=0):
        # LangChain Gemini client
        self.client = ChatGoogleGenerativeAI(
            model=model,   # or gemini-1.5-flash
            temperature=temperature
        )

    def get_ai_response(self, messages):
        try:
            # Convert your OpenAI-style messages into LangChain messages
            lc_messages = []
            for m in messages:
                if m["role"] == "system":
                    lc_messages.append(SystemMessage(content=m["content"]))
                elif m["role"] == "user":
                    lc_messages.append(HumanMessage(content=m["content"]))

            # Invoke Gemini through LangChain
            response = self.client.invoke(lc_messages)

            text = response.content.strip()

            if "```" in text:
                text = text.replace("```json", "").replace("```", "").strip()

            return text, True

        except Exception as e:
            return {"error": str(e)}, False
