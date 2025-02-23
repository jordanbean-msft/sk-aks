import logging

from semantic_kernel import Kernel
#from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from app.config import get_settings
from app.models.chat_output import ChatOutput

logger = logging.getLogger("uvicorn.error")

async def create_kubernetes_agent(client, ai_agent_settings, kernel) -> AzureAIAgent:
    code_interpreter = CodeInterpreterTool()

    agent_definition = await client.agents.create_agent(
        model=ai_agent_settings.model_deployment_name,
        name="kubernetes-agent",
        instructions="""
          You are a helpful assistant that can interpret and make recommendations for optimizing a Kubernetes cluster. You will read the CSV input which is time series data from Azure Monitor and provide recommendations for optimizing the Kubernetes cluster. You will read in the file_id provided and use your code interpreter to read the CSV file and provide recommendations for optimizing the Kubernetes cluster. You will also generate a matplotlib graph of the data.

          The CSV file will contain the following columns:
          - cluster
          - container
          - cpu
          - id
          - image
          - instance
          - job
          - name
          - namespace
          - pod
          - timestamp
          - value
        """,
        tools=code_interpreter.definitions,
        tool_resources=code_interpreter.resources
    )

    agent = AzureAIAgent(
        client=client,
        definition=agent_definition,
        kernel=kernel,
    )

    return agent

__all__ = ["create_kubernetes_agent"]
