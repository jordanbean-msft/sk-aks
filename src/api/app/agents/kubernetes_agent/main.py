import logging

from semantic_kernel import Kernel
#from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments

from app.config import get_settings
from app.models.chat_output import ChatOutput

logger = logging.getLogger("uvicorn.error")

#async def create_kubernetes_agent(kernel: Kernel) -> AzureAssistantAgent:
def create_kubernetes_agent(kernel: Kernel) -> ChatCompletionAgent:
    service_id = "azure_chat_completion"

    kernel.add_service(AzureChatCompletion(
            service_id=service_id,
            endpoint=get_settings().azure_openai_endpoint,
            api_key=get_settings().azure_openai_api_key,
            api_version=get_settings().azure_openai_api_version,
            deployment_name=get_settings().azure_openai_chat_deployment_name))

    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
    settings.response_format = ChatOutput
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    #settings.response_format = {
    #        "type": "json_schema",
    #        "json_schema": {
    #            "name": "chat_output_schema",
    #            "schema": ChatOutput.model_json_schema()
    #        },
    #        "strict": True
    #    }

    #agent = await AzureAssistantAgent.create(
    #agent = await ChatCompletionAgent.create(
    agent = ChatCompletionAgent(
                    kernel=kernel,
                    name="kubernetes-agent",
                    instructions="""You are the Kubernetes agent.
                      You are responsible for generating Kubernetes REST API calls to an Azure Kubernetes Service cluster. Use the kubernetes_rest_api plugin to take the code & make HTTP REST API calls. If the REST API call succeeds, parse the JSON result and return the answer. Make sure the output is valid JSON and conforms to the specified structured output format. 
                    """,
                    arguments=KernelArguments(settings)
                )
    
    return agent

__all__ = ["create_kubernetes_agent"]
