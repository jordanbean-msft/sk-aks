import os, logging
from typing import Annotated

from fastapi import APIRouter, Depends
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import KernelFunctionSelectionStrategy
from semantic_kernel.agents.strategies.termination.kernel_function_termination_strategy import KernelFunctionTerminationStrategy
from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.core_plugins.http_plugin import HttpPlugin

from app.config import get_settings
from app.dependencies import Dependencies
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput
from app.agents.kubernetes_agent import KubernetesAgent
from app.plugins.kubernetes_rest_api_plugin import KubernetesRestApiPlugin

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()


@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(
    dependencies: Annotated[Dependencies, Depends()], chat_input: ChatInput
) -> ChatOutput:
    return await chat(dependencies, chat_input)


async def chat(dependencies, chat_input):
    message = chat_input.message

    chat_results = await build_chat_results(dependencies, message)

    result = ChatOutput(
        thread_id=chat_input.thread_id,
        messages=chat_results
    )

    return result


async def build_chat_results(dependencies, message):
    with tracer.start_as_current_span(name="build_chat_results"):
        kernel = Kernel()
        
        kubernetes_config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data", "config.txt")

        # kubernetes_agent = await AzureAssistantAgent.create(
        #     kernel=kernel,
        #     name="kubernetes-agent",
        #     instructions="""You are the Kubernetes agent.
        #       You are responsible for generating & executing Kubernetes REST API calls to an Azure Kubernetes Service cluster. You will find a Kubernetes config file uploaded into the assistant called 'config.txt'. This file is in YAML format. Use this file to authenticate with the Kubernetes cluster. Make sure and only make REST API calls to the Kubernetes API. Do not try and use the Kubernetes Python SDK. You will send these commands to the Semantic Kernel's HttpPlugin for execution. Make sure and use the Kubernetes configuration values in the 'config.txt' file (such as the server URL, certificate authority data, client certificate data, and client key data) to authenticate with the Kubernetes cluster. Do not directly execute any code that tries to make a network call. Instead, make calls to the HttpPlugin and let it handle the network calls. You can use the 'http' plugin to make REST API calls to the Kubernetes API.
        #     """,
        #     enable_code_interpreter=True,
        #     endpoint=get_settings().azure_openai_endpoint,
        #     api_key=get_settings().azure_openai_api_key,
        #     api_version=get_settings().azure_openai_api_version,
        #     deployment_name=get_settings().azure_openai_chat_deployment_name,
        #     enable_file_search=True,
        #     code_interpreter_filenames=[kubernetes_config_file_path],
        # )
        kubernetes_agent = await AzureAssistantAgent.create(
            kernel=kernel,
            name="kubernetes-agent",
            instructions="""You are the Kubernetes agent.
              You are responsible for generating & executing Kubernetes REST API calls to an Azure Kubernetes Service cluster. Use the kubernetes_rest_api plugin to make these HTTP calls. If the REST API call succeeds, parse the JSON result and return the answer. Make sure and parse the entire result and format it so it is easy to read.
            """,
            enable_code_interpreter=False,
            endpoint=get_settings().azure_openai_endpoint,
            api_key=get_settings().azure_openai_api_key,
            api_version=get_settings().azure_openai_api_version,
            deployment_name=get_settings().azure_openai_chat_deployment_name,
            enable_file_search=False,
        )

        chat_results = []

        #http_plugin = HttpPlugin()
        #kernel.add_plugin(http_plugin, "http")
        kubernetes_rest_api_plugin = KubernetesRestApiPlugin()
        kernel.add_plugin(kubernetes_rest_api_plugin, "kubernetes_rest_api")

        thread_id = await kubernetes_agent.create_thread()

        await kubernetes_agent.add_chat_message(thread_id=thread_id,
                                                message=ChatMessageContent(role=AuthorRole.USER,
                                                                           content=message))

        try:
            async for content in kubernetes_agent.invoke(thread_id=thread_id):
                chat_results.append(content.content)
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await kubernetes_agent.delete_thread(thread_id=thread_id)
            await kubernetes_agent.delete()
        
        return chat_results
