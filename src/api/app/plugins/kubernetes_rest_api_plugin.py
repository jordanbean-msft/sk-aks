import os, logging
import urllib
import requests
from requests.models import Response
from typing import Annotated
from opentelemetry import trace

from semantic_kernel.functions.kernel_function_decorator import kernel_function

tracer = trace.get_tracer(__name__)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class KubernetesRestApiPlugin:
    @tracer.start_as_current_span(name="call_kubernetes_rest_api")
    @kernel_function(description="Executes a HTTP REST API call to the Kubernetes API")
    async def call_kubernetes_rest_api(self,
                                       method: Annotated[str, "The HTTP REST API method (GET, POST, PUT, etc) to make"],
                                       url: Annotated[str, "The HTTP REST API URL to call"],
                                       body: Annotated[str, "The HTTP REST API body to pass in"],
                                       headers: Annotated[dict, "The HTTP REST API headers to pass in"] = None,
    ) -> Annotated[Response, "The result of the HTTP REST API call"]:
        path_to_certificates = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "data")
        base_url = "https://sk-aks-dns-1fp6daak.hcp.eastus2.azmk8s.io/"

        result = requests.request(
            method=method,
            url=urllib.parse.urljoin(base_url, url),
            headers=headers,
            data=body,
            timeout=10,
            verify=(os.path.join(path_to_certificates, "ca.pem")),
            cert=(
                os.path.join(path_to_certificates, "cert.pfx"),
                os.path.join(path_to_certificates, "key.pfx")
            )
        )

        if(result.status_code == 200):
            logger.info(result.text)

        return result


__all__ = ["KubernetesRestApiPlugin"]
