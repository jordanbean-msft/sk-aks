import logging

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import AzureAssistantAgent

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")

async def create_kubernetes_agent(kernel: Kernel) -> AzureAssistantAgent:
    return await AzureAssistantAgent.create(
                    kernel=kernel,
                    name="kubernetes-agent",
                    instructions="""You are the Kubernetes agent.
                      You are responsible for generating Kubernetes REST API calls to an Azure Kubernetes Service cluster. Use the kubernetes_rest_api plugin to take the code & make HTTP REST API calls. If the REST API call succeeds, parse the JSON result and return the answer. Make sure and parse the entire result and format it so it is easy to read using Markdown. 
                    """,
                    enable_code_interpreter=True,
                    endpoint=get_settings().azure_openai_endpoint,
                    api_key=get_settings().azure_openai_api_key,
                    api_version=get_settings().azure_openai_api_version,
                    deployment_name=get_settings().azure_openai_chat_deployment_name,
                    enable_file_search=False,
                )

__all__ = ["create_kubernetes_agent"]
