import json
from typing import Dict, Any
from django.forms.models import model_to_dict
from thirdparty.movies_data_helper import get_movies_for_user
from thirdparty.app_constants import GENRE_MAPPING
from movie_agent.prompts import (
    SUGGESSTION_THROUGH_YT_DATA,
    SHARED_USR_CNT_DATA_PROMPT,
    SHARED_USR_REQUEST_PROMPT,
    TOOL_SCHEMA, DEFAULT_TOOL_ARGS
)
from movie_agent.helper.gemini_lightweight import GeminiLightClient





class MovieDataHelper:
    def __init__(self):
        self.gemini = GeminiLightClient()

    def _extract_json(self, text: str):
        text = text.strip().replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return data[0]
            return data if isinstance(data, dict) else None
        except:
            return None

    def _sanitize_tool_args(self, tool_args: Dict[str, Any], limit: int):
        clean = DEFAULT_TOOL_ARGS.copy()
        for key in clean:
            clean[key] = tool_args.get(key, clean[key])
        clean["limit"] = min(int(clean["limit"]), limit)
        if clean["genre"] and not isinstance(clean["genre"], list):
            clean["genre"] = None
        return clean

    def get_movie_suggesstion(self, user, yt_data, usr_cnt_data=None, input_txt=None, limit=10):
        prompt = SUGGESSTION_THROUGH_YT_DATA.format(yt_data=yt_data, limit=limit, genre_map=json.dumps(GENRE_MAPPING, indent=0))
        if usr_cnt_data:
            prompt += SHARED_USR_CNT_DATA_PROMPT.format(hist=json.dumps(usr_cnt_data, separators=(',', ':')))
        if input_txt:
            prompt += SHARED_USR_REQUEST_PROMPT.format(req=input_txt)
        prompt += "\n\n" + TOOL_SCHEMA

        text = self.gemini.generate(prompt)
        tool_args = self._extract_json(text)

        if tool_args is None:
            text = self.gemini.generate(prompt + "\nReturn JSON only, no explanation.", temperature=0.8)
            tool_args = self._extract_json(text)

        if tool_args is None:
            tool_args = DEFAULT_TOOL_ARGS.copy()
        print("TOOL AGRS", tool_args)
        tool_args = self._sanitize_tool_args(tool_args, limit)
        tool_args["user_id"] = user.id

        raw_results = get_movies_for_user(**tool_args)
        final = [model_to_dict(obj.content) for obj in raw_results]

        return final, True
