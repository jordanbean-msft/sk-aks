import json
import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AgentGroupChat, AzureAIAgentThread, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.core_plugins.time_plugin import TimePlugin

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents import RealtimeAudioEvent, RealtimeTextEvent
from semantic_kernel.contents.audio_content import AudioContent
from azure.ai.projects.models import ThreadMessageOptions
from semantic_kernel.connectors.ai.open_ai.services.azure_audio_to_text import AzureAudioToText
from semantic_kernel.contents import StreamingFileReferenceContent
from semantic_kernel.contents import StreamingTextContent
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    AzureRealtimeWebsocket,
    ListenEvents,
)
from semantic_kernel.contents import RealtimeAudioEvent, RealtimeTextEvent
from semantic_kernel.contents.audio_content import AudioContent
from azure.ai.projects.models import ThreadMessageOptions

from app.models.chat_input import ChatInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.plugins.azure_monitor_plugin import AzureMonitorPlugin
from app.agents.kubernetes_agent import create_kubernetes_agent
from app.agents.azure_monitor_agent import create_azure_monitor_agent
from app.config import get_settings
from app.models.content_type_enum import ContentTypeEnum
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.chat_get_image import ChatGetImageInput
from app.models.chat_get_image_contents import ChatGetImageContents
from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.routers.dependencies import AzureAIClient

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="create_thread")
@router.post("/create_thread")
async def create_thread(azure_ai_client: AzureAIClient):
        thread = await azure_ai_client.agents.create_thread()

        return ChatCreateThreadOutput(thread_id=thread.id)

@tracer.start_as_current_span(name="get_thread")
@router.get("/get_thread")
async def get_thread(thread_input: ChatGetThreadInput, azure_ai_client: AzureAIClient):
    messages = await azure_ai_client.agents.list_messages(thread_id=thread_input.thread_id)

    return_value = []

    for message in messages.data:
        return_value.append({"role": message.role, "content": message.content})

    return return_value

@tracer.start_as_current_span(name="get_image_contents")
@router.get("/get_image_contents")
async def get_file_path_annotations(thread_input: ChatGetImageContents, azure_ai_client: AzureAIClient):
    messages = await azure_ai_client.agents.list_messages(thread_id=thread_input.thread_id)

    return_value = []

    for message in messages.image_contents:
        return_value.append(
            {
                "type": message.type,
                "file_id": message.image_file.file_id,
            }
        )

    return return_value

@tracer.start_as_current_span(name="get_image")
@router.get("/get_image", response_class=Response)
async def get_image(thread_input: ChatGetImageInput, azure_ai_client: AzureAIClient):
    file_content_stream = await azure_ai_client.agents.get_file_content(thread_input.file_id)
    if not file_content_stream:
        raise RuntimeError(f"No content retrievable for file ID '{thread_input.file_id}'.")

    chunks = []
    async for chunk in file_content_stream:
        if isinstance(chunk, (bytes, bytearray)):
            chunks.append(chunk)
        else:
            raise TypeError(f"Expected bytes or bytearray, got {type(chunk).__name__}")

    image_data = b"".join(chunks)

    return Response(content=image_data, media_type="image/png")

async def thread_generator(thread):
    async for message in thread:
        yield {"role": message.role, "content": message.content}

@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    return StreamingResponse(build_chat_results(chat_input, azure_ai_client))

async def build_chat_results(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    with tracer.start_as_current_span(name="build_chat_results"):
        azure_monitor_agent = None
        kubernetes_agent = None
        try:        
            kubernetes_agent_kernel = Kernel()

            kubernetes_agent = await create_kubernetes_agent(
                client=azure_ai_client,
                kernel=kubernetes_agent_kernel
            )

            azure_monitor_kernel = Kernel()

            azure_monitor_agent = await create_azure_monitor_agent(
                client=azure_ai_client,
                kernel=azure_monitor_kernel
            )

            azure_monitor_kernel.add_plugin(
                plugin=AzureMonitorPlugin(
                    aks_cluster_name=chat_input.aks_cluster_name,
                    kubernetes_agent_id=kubernetes_agent.id,
                    thread_id=chat_input.thread_id
                ),
                plugin_name="azure_monitor"
            )

            #azure_monitor_kernel.add_plugin(TimePlugin(), plugin_name="time")

            thread = await get_agent_thread(chat_input, azure_ai_client)

            async for response in azure_monitor_agent.invoke_stream(
                thread=thread,
                messages=chat_input.content
            ):
                yield generate_chat_output(response)

            yield json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content="\n",
                    thread_id=chat_input.thread_id,
                ),
                default=serialize_chat_output,
            )

            async for response in kubernetes_agent.invoke_stream(
                thread=thread,
                messages=chat_input.content
            ):
                yield generate_chat_output(response)

            await azure_ai_client.agents.delete_agent(agent_id=azure_monitor_agent.id)
            await azure_ai_client.agents.delete_agent(agent_id=kubernetes_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            if azure_monitor_agent:
                await azure_ai_client.agents.delete_agent(agent_id=azure_monitor_agent.id)
            if kubernetes_agent:
                await azure_ai_client.agents.delete_agent(agent_id=kubernetes_agent.id)

def generate_chat_output(response):
    for item in response.items:
        if isinstance(item, StreamingTextContent):
            return json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content=response.content.content,
                    thread_id=str(response.thread.id),
                ),
                default=serialize_chat_output,                    
            )
        elif isinstance(item, StreamingFileReferenceContent):
            return json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.FILE,
                    content=item.file_id if item.file_id else "",
                    thread_id=str(response.thread.id),
                ),
                default=serialize_chat_output,                    
            )
        else:
            logger.warning(f"Unknown content type: {type(item)}")

async def get_agent_thread(chat_input, azure_ai_client):
    thread_messages = await get_thread(ChatGetThreadInput(thread_id=chat_input.thread_id), azure_ai_client)

    messages = []

    for message in thread_messages:
        msg = ThreadMessageOptions(
                    content=message['content'],
                    role=message['role']
                )
        messages.append(msg)

    thread = AzureAIAgentThread(
                client=azure_ai_client,
                thread_id=chat_input.thread_id,
                messages=messages
            )
    
    return thread