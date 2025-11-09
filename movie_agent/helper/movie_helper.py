import json
import time
import uuid
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langchain.schema import SystemMessage
from thirdparty.movies_data_helper import get_movies_for_user, search_by_date_range
from django.forms.models import model_to_dict
from thirdparty.app_constants import GENRE_MAPPING
from movie_agent.prompts import (SUGGESSTION_THROUGH_YT_DATA, SHARED_USR_CNT_DATA_PROMPT, 
    SHARED_USR_REQUEST_PROMPT)


class MovieState(TypedDict):
    messages: Annotated[list, add_messages]
    user: dict


class MovieGraph():

    def __init__(self):
        self.llm = init_chat_model(
            model_provider="openai", model="gpt-4.1"
        )

    def chat_function(self, prompt, tools):
        llm_with_tool = self.llm.bind_tools(tools=tools)
        def chat(state: MovieState):
            system_prompt = SystemMessage(content=prompt)
            messages = llm_with_tool.invoke([system_prompt] + state["messages"])
            return {"messages":messages, "user": state["user"]}
        return chat

    def movie_graph(self, prompt, tools):
        tool_node = ToolNode(tools)
        graphBuilder = StateGraph(MovieState)
        chat = self.chat_function(prompt, tools)
        graphBuilder.add_node("chat", chat)
        graphBuilder.add_node("tools", tool_node)
        graphBuilder.add_edge(START, "chat")
        graphBuilder.add_conditional_edges("chat", tools_condition)
        graphBuilder.add_edge("tools", "chat")
        graphBuilder.add_edge("chat", END)
        return graphBuilder.compile()
 

class MovieDataHelper():

    def __init__(self):
        self.movie_graph = MovieGraph()

    def get_movie_suggesstion(
            self, user, yt_data, usr_cnt_data=None, input_txt=None, limit=10):
        prompt = SUGGESSTION_THROUGH_YT_DATA.format(yt_data, limit, GENRE_MAPPING)
        if usr_cnt_data:
            prompt = prompt + SHARED_USR_CNT_DATA_PROMPT.format(
                json.dumps(usr_cnt_data, indent=2))
        if input_txt:
            prompt = prompt + SHARED_USR_REQUEST_PROMPT.format(input_txt)
        config = {"configurable": {"thread_id": user.id}}
        tools = [get_movies_for_user]
        graph = self.movie_graph.movie_graph(prompt, tools)
        messages = [{"role": "user", "content": "find top picks of moive/webseries for me using my youtube data"}]
        results = {}
        for event in graph.stream(
            {"messages": messages, "user": model_to_dict(user)}, config, stream_mode="values"):
            for message in event.get("messages", []):
                content = getattr(message, "content", None)
                if not content or not isinstance(content, str):
                    continue
                try:
                    data_list = json.loads(content)
                except json.JSONDecodeError:
                    continue 
                if isinstance(data_list, list):
                    for d in data_list:
                        imdb_id = d.get("imdbId")
                        if imdb_id and imdb_id not in results:
                            results[imdb_id] = d
        return results.values(), True
