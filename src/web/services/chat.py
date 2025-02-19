import os
import json
import requests
from msal import PublicClientApplication
from yaml import load, Loader

from models.chat_create_thread_input import ChatCreateThreadInput
from models.chat_input import ChatInput

api_base_url = os.getenv("services__api__api__0")

def get_k8s_configuration(kubernetes_cluster_name):
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

def initiate_device_flow(aks_cluster_name):
    path_to_k8s_configuration, base_url, args = get_k8s_configuration(aks_cluster_name)

    app = PublicClientApplication(client_id=args['client-id'],
                                  authority=f"https://login.microsoftonline.com/{args['tenant-id']}")
    flow = app.initiate_device_flow(scopes=[f"{args['server-id']}/.default"])

    if "user_code" not in flow:
        raise ValueError(f"Fail to create device flow. Err: {json.dumps(flow, indent=4)}")

    return flow

def get_aks_access_token(aks_cluster_name, flow):
    path_to_k8s_configuration, base_url, args = get_k8s_configuration(aks_cluster_name)

    app = PublicClientApplication(client_id=args['client-id'],
                                  authority=f"https://login.microsoftonline.com/{args['tenant-id']}")
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise ValueError(f"Fail to acquire token by device flow. Err: {json.dumps(result, indent=4)}")

    return result['access_token']

def create_agent():
    result = requests.post(url=f"{api_base_url}/v1/create_agent",
                  timeout=30)

    if result.ok:
        return result.json()['agent_id']

    return None

def create_thread(agent_id):
    chat_create_thread_input = ChatCreateThreadInput(agent_id=agent_id)

    result = requests.post(url=f"{api_base_url}/v1/create_thread",
                           json=chat_create_thread_input.model_dump(mode="json"),
                  timeout=30)
    if result.ok:
        return result.json()['thread_id']

    return None

def chat(aks_access_token,
         aks_cluster_name,
         content):

    chat_input = ChatInput(aks_access_token=aks_access_token,
                           aks_cluster_name=aks_cluster_name,
                           content=content)

    response = requests.post(url=f"{api_base_url}/v1/chat",
                               json=chat_input.model_dump(mode="json"),
                               stream=True,
                               timeout=60)

    yield from (event.decode('utf-8') for event in response)

__all__ = ["chat", "create_agent", "create_thread", "initiate_device_flow", "get_aks_access_token"]
