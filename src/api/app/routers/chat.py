import os, logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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

from app.dependencies import Dependencies
from app.models.chat_input import ChatInput
from app.plugins.kubernetes_rest_api_plugin import KubernetesRestApiPlugin
from app.agents.kubernetes_agent import create_kubernetes_agent

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(
    dependencies: Annotated[Dependencies, Depends()], chat_input: ChatInput
):
    return StreamingResponse(build_chat_results(dependencies, chat_input.message))

async def build_chat_results(dependencies, message):
    with tracer.start_as_current_span(name="build_chat_results"):
        kernel = Kernel()

        kubernetes_agent = await create_kubernetes_agent(kernel)

        kubernetes_rest_api_plugin = KubernetesRestApiPlugin()
        kernel.add_plugin(kubernetes_rest_api_plugin, "kubernetes_rest_api")

        thread_id = await kubernetes_agent.create_thread()

        await kubernetes_agent.add_chat_message(thread_id=thread_id,
                                                message=ChatMessageContent(role=AuthorRole.USER,
                                                                           content=message))

        async for content in kubernetes_agent.invoke_stream(thread_id=thread_id):
            yield content.content
