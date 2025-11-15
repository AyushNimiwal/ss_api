
# from langchain_core.tools import tool
# from mem0 import Memory
# from movie_agent.app_settings import mem_config


# class MemoryHelper():

#     def __init__(self):
#         self.mem_client = Memory.from_config(mem_config)
    
#     @tool
#     def get_memory(self, user, query):
#         """
#         Retrieve relevant memories for a user by searching stored data
#         with the given query.

#         Args:
#             user (dict): User information (must include "id").
#             query (str): The search term to filter the user's memories.

#         Returns:
#             tuple: (
#                 dict: {
#                     "code": int,        # 0 if success
#                     "data": {
#                         "user_id": str,
#                         "memory": str    # concatenated relevant memories
#                     }
#                 },
#                 bool: True if successful
#             )
#         """
#         mem_result = self.mem_client.search(query=query, user_id=user["id"])
#         memories = "\n".join([m["memory"] for m in mem_result.get("results")])
#         data = {"user_id": user["id"], "memory": memories}
#         return {"code": 0, "data": data}, True

#     @tool
#     def update_memory(self, user, agent_id, data, category):
#         """
#         Store new messages in the user's memory, tagged with agent ID
#         and category for context.

#         Args:
#             user (dict): User information (must include "id").
#             agent_id (str): Identifier of the agent storing the memory.
#             data (list|str): Messages or content to be stored.
#             category (str): Category label for the memory (e.g., "preference").

#         Returns:
#             tuple: (
#                 dict: {
#                     "code": int,         # 0 if success
#                     "message": str       # confirmation message
#                 },
#                 bool: True if successful
#             )
#         """
#         self.mem_client.add(messages=data, user_id=user["id"], 
#             metadata={"agent_id":agent_id, "category":category})
#         return {"code": 0, "message": "Messages added to memory"}, True