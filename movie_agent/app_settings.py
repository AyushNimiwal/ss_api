from django.db import models
from dotenv import load_dotenv
import os

load_dotenv()
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4.1"
LLM_TEXT_EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_STORE = "qdrant"
VECTOR_STORE_COLLECTION_NAME = "memories"
VECTOR_STORE_URL = os.getenv("QUADRANT_URL")
VECTOR_STORE_API_KEY = os.getenv("QUADRANT_KEY")
GRAPH_STORE = "neo4j"
GRAPH_STORE_URL = os.getenv("NEO4J_URI")
GRAPH_STORE_USERNAME = os.getenv("NEO4J_USERNAME")
GRAPH_STORE_PASSWORD = os.getenv("NEO4J_PASSWORD")

mem_config = {
    "version": "v1.1",
    "embedder": {
        "provider": LLM_PROVIDER,
        "config": {
            "api_key": LLM_API_KEY, 
            "model": LLM_TEXT_EMBEDDING_MODEL
        },
    },
    "llm": {
        "provider": LLM_PROVIDER, 
        "config": {
            "api_key": LLM_API_KEY, 
            "model": LLM_MODEL
        }
    },
    "vector_store": {
        "provider": VECTOR_STORE,
        "config": {
            "collection_name": VECTOR_STORE_COLLECTION_NAME,
            "url": VECTOR_STORE_URL,
            "api_key": VECTOR_STORE_API_KEY,
        },
    },
    "graph_store": {
        "provider": GRAPH_STORE,
        "config": {
            "url": GRAPH_STORE_URL,
            "username": GRAPH_STORE_USERNAME,
            "password": GRAPH_STORE_PASSWORD,
        },
    },
}

class ContentType(models.IntegerChoices):
    MOVIE = 1, "Movie"
    SHOW = 2, "Show"


# CREATE INDEX IN QDRANT DB
# from qdrant_client import QdrantClient
# from qdrant_client.models import PayloadSchemaType

# qdrant_client = QdrantClient(
#     url="https://000d7cd5-e271-4865-981d-3ea7f7583394.us-east4-0.gcp.cloud.qdrant.io", 
#     api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.cx5rB7u84G0cYfHDB7mvbI62O_8bCQHBr8k0OjaP-Kk"
# ) 

# qdrant_client.create_payload_index(
#     collection_name="memories",
#     field_name="user_id",
#     field_schema=PayloadSchemaType.KEYWORD
# )
# qdrant_client.create_payload_index(
#     collection_name="memories",
#     field_name="agent_id",
#     field_schema=PayloadSchemaType.KEYWORD
# )