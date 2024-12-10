import logging

from semantic_kernel.agents.open_ai import AzureAssistantAgent

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")

class KubernetesAgent(AzureAssistantAgent):
    def __init__(self, kernel):
        AzureAssistantAgent.__init__(
            self,
            kernel=kernel,
            name="kubernetes-agent",
            instructions="""You are the Kubernetes agent.
              You are responsible for generating & executing Kubernetes REST API calls to an Azure Kubernetes Service cluster.
            """,
            enable_code_interpreter=True,
            endpoint=get_settings().azure_openai_endpoint,
            api_key=get_settings().azure_openai_api_key,
            api_version=get_settings().azure_openai_api_version,
            deployment_name=get_settings().azure_openai_chat_deployment_name,
        )

__all__ = ["KubernetesAgent"]
