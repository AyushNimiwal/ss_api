import json
from typing import Dict, Any

from django.forms.models import model_to_dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from thirdparty.movies_data_helper import get_movies_for_user
from thirdparty.app_constants import GENRE_MAPPING
from movie_agent.prompts import (
    SUGGESSTION_THROUGH_YT_DATA,
    SHARED_USR_CNT_DATA_PROMPT,
    SHARED_USR_REQUEST_PROMPT,
    TOOL_SCHEMA
)

DEFAULT_TOOL_ARGS = {
    "title": None,
    "genre": None,
    "country": "IN",
    "language": "hi",
    "year_from": None,
    "year_until": None,
    "limit": 10,
}


class MovieDataHelper:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)

    def _extract_json(self, text: str) -> Dict[str, Any] | None:
        text = text.strip().strip("```json").strip("```")
        try:
            return json.loads(text)
        except:
            return None

    def _sanitize_tool_args(self, tool_args: Dict[str, Any], limit: int) -> Dict[str, Any]:
        clean = DEFAULT_TOOL_ARGS.copy()
        for key in clean.keys():
            clean[key] = tool_args.get(key, clean[key])
        clean["limit"] = min(int(clean["limit"]), limit)
        if clean["genre"] is not None and not isinstance(clean["genre"], list):
            clean["genre"] = None
        return clean

    def get_movie_suggesstion(
        self, user, yt_data, usr_cnt_data=None, input_txt=None, limit=10
    ):
        prompt = SUGGESSTION_THROUGH_YT_DATA.format(yt_data, limit, GENRE_MAPPING)
        if usr_cnt_data:
            prompt += SHARED_USR_CNT_DATA_PROMPT.format(json.dumps(usr_cnt_data, indent=2))
        if input_txt:
            prompt += SHARED_USR_REQUEST_PROMPT.format(input_txt)
        prompt += "\n\n" + TOOL_SCHEMA

        system_msg = SystemMessage(content=prompt)
        user_msg = HumanMessage(content="Return only the JSON arguments object.")

        llm_output = self.llm.invoke([system_msg, user_msg])
        tool_args = self._extract_json(llm_output.content)

        if tool_args is None:
            retry_msg = HumanMessage(content="Invalid JSON. Return valid JSON only.")
            llm_output = self.llm.invoke([system_msg, retry_msg])
            tool_args = self._extract_json(llm_output.content)

        if tool_args is None:
            tool_args = DEFAULT_TOOL_ARGS.copy()

        tool_args = self._sanitize_tool_args(tool_args, limit)
        tool_args["user_id"] = user.id

        raw_results = get_movies_for_user(**tool_args)
        final = [model_to_dict(obj.content) for obj in raw_results]

        return final, True
