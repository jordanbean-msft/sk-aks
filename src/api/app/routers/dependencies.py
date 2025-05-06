from functools import lru_cache
from app.config import get_settings
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from azure.ai.projects.aio import AIProjectClient
from fastapi import Depends
from typing import Annotated
from pydantic import SecretStr

def create_azure_ai_client():
    ai_agent_settings = AzureAIAgentSettings(
        model_deployment_name=get_settings().azure_openai_model_deployment_name,
        project_connection_string=SecretStr(get_settings().azure_ai_agent_project_connection_string or "")
    )

    creds = DefaultAzureCredential()

    client = AzureAIAgent.create_client(
        credential=creds,
        conn_str=ai_agent_settings.project_connection_string.get_secret_value() if ai_agent_settings.project_connection_string else ""
    )

    return client

@lru_cache
def get_create_azure_ai_client():
    return create_azure_ai_client()

AzureAIClient = Annotated[AIProjectClient, Depends(get_create_azure_ai_client)]

__all__ = ["AzureAIClient"]
