import os
import logging
from typing import Annotated
import urllib
from opentelemetry import trace
import requests
from yaml import load, Loader

from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class KubernetesRestApiPlugin:
    def __init__(self, aks_cluster_name: str, aks_access_token: str):
        self.aks_cluster_name = aks_cluster_name
        self.aks_access_token = aks_access_token

    @tracer.start_as_current_span(name="call_kubernetes_rest_api")
    @kernel_function(description="Executes a HTTP REST API call to the Kubernetes API. Make sure and only ask for the specific information you need (use filters, query, output, jsonpath, etc). The Kuberentes API can be very verbose and return a lot of JSON information.")
    async def call_kubernetes_rest_api(self,
                                       method: Annotated[str, "The HTTP REST API method (GET, POST, PUT, etc) to make"],
                                       url: Annotated[str, "The HTTP REST API URL to call"],
                                       body: Annotated[str, "The HTTP REST API body to pass in"]
    ) -> Annotated[str, "The result of the HTTP REST API call"]:
        path_to_k8s_configuration, base_url, args = self.get_k8s_configuration(kubernetes_cluster_name=self.aks_cluster_name)

        result = requests.request(
            method=method,
            url=urllib.parse.urljoin(base_url, url),
            data=body,
            timeout=10,
            headers={
                "Authorization": f"Bearer {self.aks_access_token}",
                "Content-Type": "application/json"
            },
            verify=(os.path.join(path_to_k8s_configuration, "ca.pem"))
        )

        if result.status_code == 200:
            logger.debug(f"Successfully executed Kubernetes REST API call: {result.url}")
            logger.debug(f"Body: {result.json()}")
        else:
            logger.error(f"Failed to execute Kubernetes REST API call: {result.url}")
            logger.error(f"Body: {result.json()}")

        return result.json()

    def get_k8s_configuration(self, kubernetes_cluster_name):
        path_to_k8s_configuration = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..",
            "data",
            kubernetes_cluster_name)

        with open(os.path.join(path_to_k8s_configuration, "config"), encoding="utf-8") as f:
            config = load(f, Loader=Loader)

        base_url = config['clusters'][0]['cluster']['server']

        original_args = config['users'][0]['user']['exec']['args']

        args = {}

        for arg in original_args:
            if arg.startswith("--"):
                # remove --
                arg_name = arg[2:]
                args[arg_name] = original_args[original_args.index(arg) + 1]
        return path_to_k8s_configuration,base_url,args


__all__ = ["KubernetesRestApiPlugin"]
