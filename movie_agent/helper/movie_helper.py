import json
from typing import Dict, Any
import google.generativeai as genai
import os

from django.forms.models import model_to_dict
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
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def _extract_json(self, text: str):
        text = text.strip().replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(text)

            # If Gemini returned a list instead of dict, convert safely
            if isinstance(data, list):
                # Try use first element if it's a dict
                if len(data) > 0 and isinstance(data[0], dict):
                    return data[0]
                return None

            # Otherwise return dict directly
            if isinstance(data, dict):
                return data

        except Exception:
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

        # Build the prompt
        prompt = SUGGESSTION_THROUGH_YT_DATA.format(yt_data, limit, GENRE_MAPPING)

        if usr_cnt_data:
            prompt += SHARED_USR_CNT_DATA_PROMPT.format(json.dumps(usr_cnt_data, indent=2))

        if input_txt:
            prompt += SHARED_USR_REQUEST_PROMPT.format(input_txt)

        prompt += "\n\n" + TOOL_SCHEMA
        prompt += "\nReturn ONLY the JSON arguments object."

        # Call Gemini (lightweight)
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": 0.7}
        )

        text = response.text.strip()
        tool_args = self._extract_json(text)

        # retry on invalid JSON
        if tool_args is None:
            response = self.model.generate_content(
                prompt + "\nReturn valid JSON only. No extra text.",
                generation_config={"temperature": 0.2}
            )
            tool_args = self._extract_json(response.text)

        if tool_args is None:
            tool_args = DEFAULT_TOOL_ARGS.copy()

        tool_args = self._sanitize_tool_args(tool_args, limit)
        tool_args["user_id"] = user.id

        raw_results = get_movies_for_user(**tool_args)
        final = [model_to_dict(obj.content) for obj in raw_results]

        return final, True
