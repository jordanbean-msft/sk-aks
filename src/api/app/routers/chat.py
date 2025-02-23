import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

from app.models.chat_input import ChatInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.plugins.azure_monitor_plugin import AzureMonitorPlugin
from app.agents.kubernetes_agent import create_kubernetes_agent
from app.agents.azure_monitor_agent import create_azure_monitor_agent
from app.config import get_settings
from app.models.content_type_enum import ContentTypeEnum
from app.models.chat_output import ChatOutput
from app.models.chat_get_image import ChatGetImageInput
from app.models.chat_get_image_contents import ChatGetImageContents
from app.models.chat_create_thread_output import ChatCreateThreadOutput

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="create_thread")
@router.post("/create_thread")
async def create_thread():
    ai_agent_settings = AzureAIAgentSettings(
                model_deployment_name=get_settings().azure_openai_model_deployment_name,
                project_connection_string=get_settings().azure_ai_agent_project_connection_string
            )
    async with (
        DefaultAzureCredential() as creds,

        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value()
        ) as client,
    ):

        thread = await client.agents.create_thread()

        return ChatCreateThreadOutput(thread_id=thread.id)

@tracer.start_as_current_span(name="get_thread")
@router.get("/get_thread")
async def get_thread(thread_input: ChatGetThreadInput):
    ai_agent_settings = AzureAIAgentSettings(
                model_deployment_name=get_settings().azure_openai_model_deployment_name,
                project_connection_string=get_settings().azure_ai_agent_project_connection_string
            )
    async with (
        DefaultAzureCredential() as creds,

        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value()
        ) as client,
    ):

        messages = await client.agents.list_messages(thread_id=thread_input.thread_id)

        return_value = []

        for message in messages.data:
            return_value.append({"role": message.role, "content": message.content})

        return return_value

@tracer.start_as_current_span(name="get_image_contents")
@router.get("/get_image_contents")
async def get_file_path_annotations(thread_input: ChatGetImageContents):
    ai_agent_settings = AzureAIAgentSettings(
                model_deployment_name=get_settings().azure_openai_model_deployment_name,
                project_connection_string=get_settings().azure_ai_agent_project_connection_string
            )
    async with (
        DefaultAzureCredential() as creds,

        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value()
        ) as client,
    ):

        messages = await client.agents.list_messages(thread_id=thread_input.thread_id)

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
async def get_image(thread_input: ChatGetImageInput):
    ai_agent_settings = AzureAIAgentSettings(
        model_deployment_name=get_settings().azure_openai_model_deployment_name,
        project_connection_string=get_settings().azure_ai_agent_project_connection_string
    )
    async with (
        DefaultAzureCredential() as creds,

        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value()
        ) as client,
    ):
        file_content_stream = await client.agents.get_file_content(thread_input.file_id)
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
async def post_chat(chat_input: ChatInput):
    return StreamingResponse(build_chat_results(chat_input))

async def build_chat_results(chat_input: ChatInput):
    with tracer.start_as_current_span(name="build_chat_results"):
        try:
            ai_agent_settings = AzureAIAgentSettings(
                model_deployment_name=get_settings().azure_openai_model_deployment_name,
                project_connection_string=get_settings().azure_ai_agent_project_connection_string
            )
            async with (
                DefaultAzureCredential() as creds,

                AzureAIAgent.create_client(
                    credential=creds,
                    conn_str=ai_agent_settings.project_connection_string.get_secret_value()
                ) as client,
            ):
                new_kernel = Kernel()

                kubernetes_agent = await create_kubernetes_agent(
                    client=client,
                    ai_agent_settings=ai_agent_settings,
                    kernel=new_kernel
                )

                kernel = Kernel()

                azure_monitor_agent = await create_azure_monitor_agent(
                    client=client,
                    ai_agent_settings=ai_agent_settings,
                    kernel=kernel
                )

                kernel.add_plugin(
                    plugin=AzureMonitorPlugin(
                        aks_cluster_name=chat_input.aks_cluster_name,
                        kubernetes_agent_id=kubernetes_agent.id,
                        thread_id=chat_input.thread_id
                    ),
                    plugin_name="azure_monitor"
                )

                for message in chat_input.content:
                    await azure_monitor_agent.add_chat_message(
                        thread_id=chat_input.thread_id,
                        message=ChatMessageContent(role=message.role, content=message.content)
                    )

                async for content in azure_monitor_agent.invoke_stream(thread_id=chat_input.thread_id):
                    yield content.content

                async for content in kubernetes_agent.invoke_stream(thread_id=chat_input.thread_id):
                    yield content.content

                await client.agents.delete_agent(assistant_id=azure_monitor_agent.id)
                await client.agents.delete_agent(assistant_id=kubernetes_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            await client.agents.delete_agent(assistant_id=azure_monitor_agent.id)
            await client.agents.delete_agent(assistant_id=kubernetes_agent.id)
