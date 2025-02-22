import logging
import urllib
import json
from typing import Annotated
import requests
from opentelemetry import trace
from msal import ConfidentialClientApplication

from semantic_kernel.functions.kernel_function_decorator import kernel_function

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class AzureMonitorPlugin:
    def __init__(self, aks_cluster_name: str):
        self.aks_cluster_name = aks_cluster_name

    @tracer.start_as_current_span(name="call_azure_monitor")
    @kernel_function(description="Executes a HTTP REST API call to the Azure Monitor API, using the Prometheus query language (PromQL) for querying and aggregating metrics & time series data.")
    async def call_azure_monitor(self,
                                method: Annotated[str, "The HTTP REST API method (GET, POST) to make"],
                                url: Annotated[str, "The HTTP REST API URL to call. This should only be the Prometheus HTTP API path (using the v1 API specification), not the full URL"],
                                params: Annotated[str, "The HTTP REST API query parameters to pass in. This should be a valid query string to append to the URL."],
                                body: Annotated[str,
                                                "The HTTP REST API body to pass in. This should be a valid PromQL query if the method is POST."]
                                ) -> Annotated[str, "The result of the HTTP REST API call"]:
        access_token = get_azure_monitor_access_token()

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

        if result.status_code == 200:
            logger.debug(
                f"Successfully executed Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.debug(f"Body: {result.json()}")
        else:
            logger.error(
                f"Failed to execute Azure Monitor REST API call: {result.request.method}: {result.url}")
            logger.error(f"Body: {result.json()}")

        return result.json()


def get_azure_monitor_access_token():
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

__all__ = ["AzureMonitorPlugin",]
