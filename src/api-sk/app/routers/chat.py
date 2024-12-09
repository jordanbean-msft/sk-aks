import logging
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

from app.config import get_settings
from app.dependencies import Dependencies
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput
from app.agents.kubernetes_agent import KubernetesAgent

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

        # settings = kernel.get_prompt_execution_settings_from_service_id(
        #     service_id="default")
        # settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        #kernel.add_plugin(KubernetesPlugin(), plugin_name="KubernetesPlugin")

        # kubernetes_agent = await create_agents(kernel)
        kubernetes_agent = await AzureAssistantAgent.create(
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

        # termination_function = create_termination_function()

        # selection_function = create_selection_function(stock_agent, news_agent)

        # chat = AgentGroupChat(
        #     agents=[
        #         stock_agent,
        #         news_agent
        #     ],
        #     selection_strategy=KernelFunctionSelectionStrategy(
        #         function=selection_function,
        #         kernel=kernel,
        #         result_parser=lambda result: str(
        #             result.value[0]) if result.value is not None else news_agent.name,
        #         agent_variable_name="agents",
        #         history_variable_name="history"
        #     ),
        #     termination_strategy=KernelFunctionTerminationStrategy(
        #         agents=[news_agent],
        #         function=termination_function,
        #         kernel=kernel,
        #         result_parser=lambda result: str(
        #             result.value[0]).lower() == "yes",
        #         history_variable_name="history",
        #         maximum_iterations=10
        #     )
        # )

        # await chat.add_chat_message(ChatMessageContent(
        #     role=AuthorRole.USER,
        #     content=message
        # ))

        chat_results = []

        # async for content in chat.invoke():
        #     chat_results.append(content.content)

        # return chat_results

        thread_id = await kubernetes_agent.create_thread()

        await kubernetes_agent.add_chat_message(thread_id=thread_id,
                                                message=ChatMessageContent(role=AuthorRole.USER, 
                                                                           content=message))

        async for content in kubernetes_agent.invoke(thread_id=thread_id):
            chat_results.append(content.content)

        return chat_results
        #finally:
        #    await agent.delte_thread(thread_id)


# def create_selection_function(stock_agent, news_agent):
#     selection_function = KernelFunctionFromPrompt(
#         function_name="selection",
#         prompt=f"""
#                 Determine which participant takes the next turn in a conversation based on the the most recent participant.
#                 State only the name of the participant to take the next turn.
#                 No participant should take more than one turn in a row.
#                 Choose only from these participants:
#                 - {stock_agent.name}
#                 - {news_agent.name}
#                 Always follow these rules when selecting the next participant:
#                 - After user input, it is {stock_agent.name}'s turn.
#                 - After {stock_agent.name} replies, it is {news_agent.name}'s turn.
#                 History:
#                 {{{{$history}}}}
#             """
#     )

#     return selection_function


# def create_termination_function():
#     termination_function = KernelFunctionFromPrompt(
#         function_name="termination",
#         prompt="""
#             Determine if the stock data has been analyzed together with the news data.  If so, respond with a single word: yes
#             History:
#             {{$history}}
#             """,
#     )

#     return termination_function


async def create_agents(kernel):
    # stock_agent = StockAgent(
    #     kernel=kernel,
    #     execution_settings=settings
    # )

    # news_agent = KubectlAgent(
    #     kernel=kernel,
    #     execution_settings=settings
    # )

    # return stock_agent, news_agent
    kubernetes_agent = KubernetesAgent(
        kernel=kernel
    )

    kubernetes_agent = await kubernetes_agent.create_assistant()

    return kubernetes_agent
