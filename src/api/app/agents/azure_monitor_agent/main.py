import logging
from datetime import datetime

from semantic_kernel import Kernel
#from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from app.config import get_settings
from app.models.chat_output import ChatOutput

logger = logging.getLogger("uvicorn.error")

#async def create_azure_monitor_agent(client, kernel, name, plugins) -> AzureAIAgent:
async def create_azure_monitor_agent(client, kernel, name, plugins) -> ChatCompletionAgent:
    # agent_definition = await client.agents.create_agent(
    #     model=get_settings().azure_openai_model_deployment_name,
    #     name=name,
    #     instructions=f"""
    #       You are a helpful assistant that can query Azure Monitor for Kubernetes Prometheus monitoring logs. If you are unable to retrieve any data for the specified datatype & time, do not make it up. Return a message indicating that no data was found. Make sure you call your provided functions to retrieve the Azure Monitor data based upon the user's query. You will upload a file with the results of the query. This will result in the file ID returned to you.
    #     """
    # )

    #agent = AzureAIAgent(
    agent = ChatCompletionAgent(
        #client=client,
        #definition=agent_definition.,
        name=name,
        instructions="""
          You are a helpful assistant that can query Azure Monitor for Kubernetes Prometheus monitoring logs. If you are unable to retrieve any data for the specified datatype & time, do not make it up. Return a message indicating that no data was found. Once you have successfully retrieved the data, reply back that you have retrieved the data and provide the file id.
        """,
        kernel=kernel,
        plugins=plugins
    )

    return agent

__all__ = ["create_azure_monitor_agent"]
