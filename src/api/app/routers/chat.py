import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

from app.models.chat_input import ChatInput
from app.models.chat_create_thread_input import ChatCreateThreadInput
from app.models.chat_get_thread import ChatGetThreadInput
from app.plugins.kubernetes_rest_api_plugin import KubernetesRestApiPlugin
from app.plugins.azure_monitor_plugin import AzureMonitorPlugin
from app.agents.kubernetes_agent import create_kubernetes_agent
from app.agents.azure_monitor_agent import create_azure_monitor_agent
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

# @tracer.start_as_current_span(name="create_agent")
# @router.post("/create_agent")
# async def post_create_agent():
#     kernel = Kernel()

#     kubernetes_agent = await create_kubernetes_agent(kernel)

#     return {"agent_id": kubernetes_agent.assistant.id}

# @tracer.start_as_current_span(name="get_agent")
# @router.get("/get_agent")
# async def get_agent(agent_id: str):
#     kernel = Kernel()

#     kubernetes_agent = await AzureAssistantAgent.retrieve(
#         id=agent_id,
#         kernel=kernel,
#         endpoint=get_settings().azure_openai_endpoint,
#         api_key=get_settings().azure_openai_api_key,
#         api_version=get_settings().azure_openai_api_version
#         )

#     if not kubernetes_agent:
#         return {"error": f"Agent with ID {agent_id} not found"}

#     return kubernetes_agent

# @tracer.start_as_current_span(name="create_thread")
# @router.post("/create_thread")
# async def post_create_thread(agent_input: ChatCreateThreadInput):
#     kernel = Kernel()

#     kubernetes_agent = await AzureAssistantAgent.retrieve(
#         id=agent_input.agent_id,
#         kernel=kernel,
#         endpoint=get_settings().azure_openai_endpoint,
#         api_key=get_settings().azure_openai_api_key,
#         api_version=get_settings().azure_openai_api_version
#         )

#     if not kubernetes_agent:
#         return {"error": f"Agent with ID {agent_input.agent_id} not found"}

#     thread_id = await kubernetes_agent.create_thread()

#     return {"thread_id": thread_id}

# @tracer.start_as_current_span(name="get_thread")
# @router.get("/get_thread")
# async def get_thread(thread_input: ChatGetThreadInput):
#     kernel = Kernel()

#     kubernetes_agent = await AzureAssistantAgent.retrieve(
#         id=thread_input.agent_id,
#         kernel=kernel,
#         endpoint=get_settings().azure_openai_endpoint,
#         api_key=get_settings().azure_openai_api_key,
#         api_version=get_settings().azure_openai_api_version
#         )

#     if not kubernetes_agent:
#         return {"error": f"Agent with ID {thread_input.agent_id} not found"}

#     thread = kubernetes_agent.get_thread_messages(thread_input.thread_id)

#     real_thread_messages = []
#     real_run_messages = []
#     real_thread = await kubernetes_agent.client.beta.threads.messages.list(thread_id=thread_input.thread_id)

#     for message in real_thread.data:
#         if message.run_id is not None:
#             run_steps = await kubernetes_agent.client.beta.threads.runs.steps.list(thread_id=thread_input.thread_id, run_id = message.run_id)
#             for run_step in run_steps.data:
#                 real_run_messages.append(run_step)
#         real_thread_messages.append(message)

#     if not thread:
#         return {"error": f"Thread with ID {thread_input.thread_id} not found"}

#     return_value = []

#     async for chunk in thread_generator(thread):
#         return_value.append(chunk)

#     return return_value

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
            
                thread = await client.agents.create_thread()

                kernel = Kernel()

                azure_monitor_agent = await create_azure_monitor_agent(
                    client=client,
                    ai_agent_settings=ai_agent_settings,
                    kernel=kernel
                )

                kernel.add_plugin(plugin=AzureMonitorPlugin(aks_cluster_name=chat_input.aks_cluster_name),
                                plugin_name="azure_monitor")
                
                new_kernel = Kernel()

                kubernetes_agent = await create_kubernetes_agent(
                    client=client,
                    ai_agent_settings=ai_agent_settings,
                    kernel=new_kernel
                )                

                for message in chat_input.content:
                    await azure_monitor_agent.add_chat_message(
                        thread_id=thread.id,
                        message=ChatMessageContent(role=message.role, content=message.content)
                    )

                async for content in azure_monitor_agent.invoke(thread_id=thread.id):
                    #logger.debug(content.content)
                    yield content.content

                async for content in kubernetes_agent.invoke_stream(thread_id=thread.id):
                    yield content.content

                await client.agents.delete_thread(thread_id=thread.id)
                await client.agents.delete_agent(assistant_id=azure_monitor_agent.id)
                await client.agents.delete_agent(assistant_id=kubernetes_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            await client.agents.delete_thread(thread_id=thread.id)
            await client.agents.delete_agent(assistant_id=azure_monitor_agent.id)
            await client.agents.delete_agent(assistant_id=kubernetes_agent.id)
