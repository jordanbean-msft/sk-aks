import asyncio
from functools import lru_cache

from openai import AsyncAzureOpenAI
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

async def create_async_azure_ai_client():
    project_client = AIProjectClient.from_connection_string(conn_str=get_settings().azure_ai_agent_project_connection_string, credential=DefaultAzureCredential())

    async_azure_ai_client = await project_client.inference.get_azure_openai_client()

    return async_azure_ai_client

@lru_cache
def get_create_azure_ai_client():
    return create_azure_ai_client()

@lru_cache
async def get_create_async_azure_ai_client():
    return await create_async_azure_ai_client()

AzureAIClient = Annotated[AIProjectClient, Depends(get_create_azure_ai_client)]
AsyncAzureAIClient = Annotated[AsyncAzureOpenAI, Depends(get_create_async_azure_ai_client)]

__all__ = ["AzureAIClient", "AsyncAzureAIClient"]
