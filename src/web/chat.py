import os
import requests

api_base_url = os.getenv("services__api__api__0")

def create_agent():
    result = requests.post(url=f"{api_base_url}/v1/create_agent",
                  timeout=30)

    if result.ok:
        return result.json()['agent_id']

    return None

def create_thread(agent_id):
    result = requests.post(url=f"{api_base_url}/v1/create_thread",
                  json={"agent_id": agent_id},
                  timeout=30)
    if result.ok:
        return result.json()['thread_id']

    return None

def chat(agent_id, thread_id, content):
    for event in requests.post(url=f"{api_base_url}/v1/chat",
                               json={
                                    "agent_id": agent_id,
                                    "thread_id": thread_id,
                                    "content": content
                               },
                               stream=True,
                               timeout=30):
        yield event.decode('utf-8')

__all__ = ["chat"]
