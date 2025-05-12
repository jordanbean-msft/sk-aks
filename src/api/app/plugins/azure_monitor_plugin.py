from datetime import datetime
import logging
import urllib
import json
import csv
from typing import Annotated
import requests
from opentelemetry import trace
from msal import ConfidentialClientApplication

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class AzureMonitorPlugin:
    def __init__(self, aks_cluster_name: str, kubernetes_agent_id: str, thread_id: str):
        self.aks_cluster_name = aks_cluster_name
        self.kubernetes_agent_id = kubernetes_agent_id
        self.thread_id = thread_id

    @tracer.start_as_current_span(name="call_azure_monitor_generic")
    #@kernel_function(description="Executes a HTTP REST API call to the Azure Monitor API, using the Prometheus query language (PromQL) for querying and aggregating metrics & time series data.")
    async def call_azure_monitor_generic(self,
                                method: Annotated[str, "The HTTP REST API method (GET, POST) to make"],
                                url: Annotated[str, "The HTTP REST API URL to call. This should only be the Prometheus HTTP API path (using the v1 API specification)"],
                                params: Annotated[str, "The HTTP REST API query parameters to append to the URL. Start and End parameters must be in RFC3339 format."],
                                body: Annotated[str,
                                                "The HTTP REST API body to pass in. This should be a valid PromQL query if the method is POST."]
                                ) -> Annotated[str, "The result of the HTTP REST API call"]:
        access_token = self.get_azure_monitor_access_token()

        if method == "GET":
            result = requests.request(
                method=method,
                url=urllib.parse.urljoin(get_settings().azure_monitor_query_endpoint, url),
                params=params,
                timeout=10,
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )
        elif method == "POST":
            result = requests.request(
                method=method,
                url=urllib.parse.urljoin(get_settings().azure_monitor_query_endpoint, url),
                params=params,
                data=urllib.parse.quote(body),
                timeout=10,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

        if result.ok:
            logger.debug(
                f"Successfully executed Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.debug(f"Body: {result.json()}")

            try:
                file_upload_id = await self.process_result(result)
                return file_upload_id
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                return f"Error processing chat: {e}"
        else:
            logger.error(
                f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.error(f"Body: {result.json()}")

            return f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url} - {result.json()}"
        
    @tracer.start_as_current_span(name="call_azure_monitor_hard_coded")
    #@kernel_function(description="Executes a HTTP REST API call to the Azure Monitor API, using the Prometheus query language (PromQL) for querying and aggregating metrics & time series data.")
    async def call_azure_monitor_hard_coded(self) -> Annotated[str, "The result of the HTTP REST API call"]:
        access_token = self.get_azure_monitor_access_token()

        result = requests.request(
            method="GET",
            url=urllib.parse.urljoin(get_settings().azure_monitor_query_endpoint, "/api/v1/query_range"),
            params="query=rate(container_cpu_usage_seconds_total{namespace=\"azure-store\"}[30d])&start=1746410700&end=1746497100&step=1d",
            timeout=10,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if result.ok:
            logger.debug(
                f"Successfully executed Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.debug(f"Body: {result.json()}")

            try:
                file_upload_id = await self.process_result(result)
                return file_upload_id
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                return f"Error processing chat: {e}"
        else:
            logger.error(
                f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.error(f"Body: {result.json()}")

            return f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url} - {result.json()}"

    # @tracer.start_as_current_span(name="get_current_time")
    # @kernel_function(description="Returns the current time in Unix timestamp format.")
    # async def get_current_time(self) -> Annotated[int, "The current time in Unix timestamp format"]:
    #     logger.debug(f"Getting current time {datetime.now().timestamp()}")
    #     return int(datetime.now().timestamp())

    @tracer.start_as_current_span(name="call_azure_monitor")
    @kernel_function(description="Executes call to the Azure Monitor API, using the Prometheus query language (PromQL) for querying and aggregating metrics & time series data for a Azure Kubernetes Cluster. This will return the container cpu usage seconds total.")
    async def call_azure_monitor(self,
            namespace: Annotated[str, "The Kubernetes namespace to filter on"],
            number_of_days: Annotated[str, "The time range to query for. Should include the time unit (e.g. 30d, 1h)"],
            start: Annotated[int, "The Unix timestamp of the start of the range. Make sure and determine this time based upon the current time. Make sure this start time is not more than 32 days before the end time"],
            end: Annotated[int, "The Unix timestamp of the end of the range. Make sure and determine this time based upon the current time. Make sure this end time is not more than 32 days later than the start time"],
            step: Annotated[str, "The resolution of the data to return"]) -> Annotated[str, "The number of container cpu usage seconds total"]:
        access_token = self.get_azure_monitor_access_token()

        result = requests.request(
            method="GET",
            url=urllib.parse.urljoin(get_settings().azure_monitor_query_endpoint, "/api/v1/query_range"),
            params=f'query=rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[{number_of_days}])&start={start}&end={end}&step={step}',
            timeout=10,
            headers={
            "Authorization": f"Bearer {access_token}"
            }
        )

        if result.ok:
            logger.debug(
                f"Successfully executed Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.debug(f"Body: {result.json()}")

            try:
                file_upload_id = await self.process_result(result)
                return file_upload_id
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                return f"Error processing chat: {e}"
        else:
            logger.error(
                f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.error(f"Body: {result.json()}")

            return f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url} - {result.json()}"


    def get_azure_monitor_access_token(self):
            settings = get_settings()

            app = ConfidentialClientApplication(
                client_id=settings.client_id,
                client_credential=settings.client_secret,
                authority=f"https://login.microsoftonline.com/{settings.tenant_id}"
            )

            result = app.acquire_token_for_client(
                scopes=["https://prometheus.monitor.azure.com/.default"])

            if "access_token" not in result:
                raise ValueError(
                    f"Fail to acquire token by device flow. Err: {json.dumps(result, indent=4)}")

            return result['access_token']

    async def process_result(self, result):
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
            # Write the JSON result to a file
            file_path = "azure_monitor_result.json"
            with open(file=file_path, mode="w", encoding="utf-8") as file:
                json.dump(result.json(), file)

            csv_file_path = "azure_monitor_result.csv"
            with open(file=csv_file_path, mode="w", encoding="utf-8") as csv_file:
                data = result.json()
                csv_writer = csv.writer(csv_file)
                # Write the header
                header = ["cluster", "container", "cpu", "id", "image", "instance", "job", "name", "namespace", "pod", "timestamp", "value"]
                csv_writer.writerow(header)

                # Write the data
                for result in data["data"]["result"]:
                    metric = result["metric"]
                    for value in result["values"]:
                        row = [
                            metric.get("cluster", ""),
                            metric.get("container", ""),
                            metric.get("cpu", ""),
                            metric.get("id", ""),
                            metric.get("image", ""),
                            metric.get("instance", ""),
                            metric.get("job", ""),
                            metric.get("name", ""),
                            metric.get("namespace", ""),
                            metric.get("pod", ""),
                            value[0],
                            value[1]
                        ]
                        csv_writer.writerow(row)

            # Upload the file to the Azure AI agent
            file_upload = await client.agents.upload_file(
                #file_path=file_path,
                file_path=csv_file_path,
                purpose="assistants"
            )

            kubernetes_agent = await client.agents.get_agent(agent_id=self.kubernetes_agent_id)

            code_interpreter = CodeInterpreterTool(
                file_ids=[file_upload.id]
            )

            await client.agents.update_agent(
                agent_id=kubernetes_agent.id,
                tools=code_interpreter.definitions,
                tool_resources=code_interpreter.resources
            )

            return file_upload.id

__all__ = ["AzureMonitorPlugin",]
