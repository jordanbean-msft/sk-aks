from functools import lru_cache

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_endpoint: str
    azure_openai_api_version: str
    azure_openai_chat_deployment_name: str
    azure_openai_embedding_deployment_name: str
    azure_openai_api_key: str
    application_insights_connection_string: str
    client_id: str
    client_secret: str
    tenant_id: str
    azure_monitor_query_endpoint: str

@lru_cache
def get_settings():
    return Settings()

__all__ = ["get_settings"]
