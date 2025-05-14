import json
import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from openai import AsyncAzureOpenAI

from semantic_kernel import Kernel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AgentGroupChat, AzureAIAgentThread, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.contents.chat_history import ChatHistory

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
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistoryTruncationReducer
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from azure.ai.projects.aio import AIProjectClient

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
from app.routers.dependencies import AsyncAzureAIClient, AzureAIClient

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

KUBERNETES_AGENT_NAME = "kubernetes-agent"
AZURE_MONITOR_AGENT_NAME = "azure-monitor-agent"

# Define a selection function to determine which agent should take the next turn.
SELECTION_FUNCTION = KernelFunctionFromPrompt(
        function_name="selection",
        prompt=f"""
Examine the provided RESPONSE and choose the next participant.
State only the name of the chosen participant without explanation.

Choose only from these participants:
- {KUBERNETES_AGENT_NAME}
- {AZURE_MONITOR_AGENT_NAME}

Rules:
- If RESPONSE is user input, it is {AZURE_MONITOR_AGENT_NAME}'s turn.
- If RESPONSE is by {AZURE_MONITOR_AGENT_NAME} and the result includes a file ID (in the format of 'assistant-Z6BLrvg6p37LcqL05uyRqp'), it is {KUBERNETES_AGENT_NAME} turn. Otherwise, choose {AZURE_MONITOR_AGENT_NAME} again.

RESPONSE:
{{{{$history}}}}
""",
)

# Define a termination function where the reviewer signals completion with "yes".
TERMINATION_KEYWORD = "yes"

TERMINATION_FUNCTION = KernelFunctionFromPrompt(
        function_name="termination",
        prompt=f"""
Examine the RESPONSE and determine whether the content has been deemed satisfactory.
If the content is satisfactory, respond with a single word without explanation: {TERMINATION_KEYWORD}.
If specific suggestions are being provided, it is not satisfactory.
If no correction is suggested, it is satisfactory.

RESPONSE:
{{{{$history}}}}
""",
    )

history_reducer = ChatHistoryTruncationReducer(target_count=10)

async def create_async_azure_ai_client():
    project_client = AIProjectClient.from_connection_string(conn_str=get_settings().azure_ai_agent_project_connection_string, credential=DefaultAzureCredential())

    async_azure_ai_client = await project_client.inference.get_azure_openai_client(api_version=get_settings().azure_openai_api_version)

    return async_azure_ai_client

def _create_kernel_with_chat_completion(service_id: str, client) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id,
                                           deployment_name=get_settings().azure_openai_model_deployment_name,
                                           async_client=client
                                           )
    )
    kernel.add_service(AzureChatCompletion(service_id="selection",
                                           deployment_name=get_settings().azure_openai_model_deployment_name,
                                           async_client=client
                                           )
    )
    kernel.add_service(AzureChatCompletion(service_id="termination",
                                           deployment_name=get_settings().azure_openai_model_deployment_name,
                                           async_client=client
                                           )
    )
    return kernel

@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    return StreamingResponse(build_chat_results(chat_input, azure_ai_client))

async def build_chat_results(chat_input: ChatInput, azure_ai_client: AzureAIClient):
    with tracer.start_as_current_span(name="build_chat_results"):
        azure_monitor_agent = None
        kubernetes_agent = None
        try:        
            async_azure_ai_client = await create_async_azure_ai_client()
            kernel = _create_kernel_with_chat_completion("", async_azure_ai_client)

            kubernetes_agent = await create_kubernetes_agent(
                client=azure_ai_client,
                kernel=kernel,
                name=KUBERNETES_AGENT_NAME
            )

            azure_monitor_plugin=AzureMonitorPlugin(
                aks_cluster_name=chat_input.aks_cluster_name,
                kubernetes_agent_id=kubernetes_agent.id,
                thread_id=chat_input.thread_id
            )

            time_plugin = TimePlugin()
            math_plugin = MathPlugin()

            azure_monitor_agent = await create_azure_monitor_agent(
                client=azure_ai_client,
                kernel=kernel, 
                name=AZURE_MONITOR_AGENT_NAME,
                plugins=[azure_monitor_plugin, time_plugin, math_plugin]
            )

            thread = await get_agent_thread(chat_input, azure_ai_client)

            chat_history = ChatHistory()

            async for message in thread.get_messages():
                chat_history.add_message(
                    ChatMessageContent(
                        content=message.content,
                        role=AuthorRole(message.role),
                    )
                )

            chat_history.add_message(
                ChatMessageContent(
                    content=chat_input.content,
                    role=AuthorRole.USER,
                )
            )

            # Create the AgentGroupChat with selection and termination strategies.
            chat = AgentGroupChat(
                agents=[kubernetes_agent, azure_monitor_agent],
                selection_strategy=KernelFunctionSelectionStrategy(
                    initial_agent=azure_monitor_agent,
                    function=SELECTION_FUNCTION,
                    kernel=kernel,
                    result_parser=result_parser_selection,
                    history_variable_name="history",
                    history_reducer=history_reducer,
                    agent_variable_name="agents"
                ),
                termination_strategy=KernelFunctionTerminationStrategy(
                    agents=[kubernetes_agent],
                    function=TERMINATION_FUNCTION,
                    kernel=kernel,
                    result_parser=result_parser_termination,
                    history_variable_name="history",
                    maximum_iterations=10,
                    history_reducer=history_reducer,
                ),
                #chat_history=chat_history
            )

            await chat.add_chat_message(
                ChatMessageContent(
                    content=chat_input.content,
                    role=AuthorRole.USER,
                )
            )

            message = ""
            try:
                #async for response in chat.invoke():
                async for response in chat.invoke_stream():
                    if response is None or not response.name:
                        continue
                    msg = generate_chat_output(response)                    
                    yield msg
            except Exception as e:
                logger.error(f"Error during chat invocation: {e}")
                yield generate_text_output(f"Error during chat invocation: {e}")

             
            await azure_ai_client.agents.delete_agent(agent_id=kubernetes_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            yield generate_text_output(f"Error during chat invocation: {e}")

            #if azure_monitor_agent:
            #    await azure_ai_client.agents.delete_agent(agent_id=azure_monitor_agent.id)
            if kubernetes_agent:
                await azure_ai_client.agents.delete_agent(agent_id=kubernetes_agent.id)

def result_parser_selection(result):
    x = str(result.value[0]).strip() if result.value[0] is not None else KUBERNETES_AGENT_NAME
    return x

def result_parser_termination(result):
    x = TERMINATION_KEYWORD in str(result.value[0]).lower()
    return x

def generate_text_output(response):
    return json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content=response,
                    thread_id=""#str(response.thread.id),
                ),
                default=serialize_chat_output,                    
            )

def generate_chat_output(response):
    for item in response.items:
        if isinstance(item, StreamingTextContent):
            return json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content=item.text,
                    thread_id=""#str(response.thread.id),
                ),
                default=serialize_chat_output,                    
            )
        elif isinstance(item, StreamingFileReferenceContent):
            return json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.FILE,
                    content=item.file_id if item.file_id else "",
                    thread_id=""#str(response.thread.id),
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