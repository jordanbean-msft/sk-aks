import os
import json
import requests
from msal import PublicClientApplication
from yaml import load, Loader
from websockets.sync.client import connect

from models.chat_input import ChatInput
from models.chat_get_thread import ChatGetThreadInput
from models.chat_get_image import ChatGetImageInput
from models.chat_get_image_contents import ChatGetImageContents
from models.chat_realtime_input import ChatRealtimeInput

api_base_url = os.getenv("services__api__api__0", "")

def create_thread():
    result = requests.post(url=f"{api_base_url}/v1/create_thread",
                  timeout=30)
    if result.ok:
        return result.json()['thread_id']

    return None

def chat(thread_id,
         aks_cluster_name,
         content):

    chat_input = ChatInput(thread_id=thread_id,
                           aks_cluster_name=aks_cluster_name,
                           content=content)

    response = requests.post(url=f"{api_base_url}/v1/chat",
                               json=chat_input.model_dump(mode="json"),
                               stream=True,
                               timeout=300
                )

    yield from (event.decode('utf-8') for event in response)

def realtime(content):
    #remove http(s) from api_base_url
    raw_api_base_url = api_base_url.replace("http://", "").replace("https://", "")

    try:
        with connect(f"ws://{raw_api_base_url}/v1/realtime",
                      timeout=30) as ws:
            # Send audio bytes
            ws.send(content)  # content should be bytes

            ws.send("END")  # Send a message to indicate the end of the audio stream

            while True:
                result = ws.recv()
                if result == "END":
                    break
                yield result
    except Exception as e:
        print(f"Error in realtime connection: {e}")

def transcribe(content):
    try:
        response = requests.post(url=f"{api_base_url}/v1/transcribe",
                                 files={"file": content},
                                 timeout=60)
        return response.json()
    except Exception as e:
        print(f"Error during transcription: {e}")

def get_thread(thread_id):
    get_thread_input = ChatGetThreadInput(thread_id=thread_id)

    response = requests.get(url=f"{api_base_url}/v1/get_thread",
                            data=get_thread_input.model_dump(mode="python"),
                            timeout=60)

    return response.json()

def get_image(file_id):
    get_image_input = ChatGetImageInput(file_id=file_id)

    image = requests.get(
        url=f"{api_base_url}/v1/get_image",
        json=get_image_input.model_dump(mode="json"),
        timeout=60
    )

    return image.content

def get_image_contents(thread_id):
    get_image_input = ChatGetImageContents(thread_id=thread_id)

    image_contents = requests.get(
        url=f"{api_base_url}/v1/get_image_contents",
        json=get_image_input.model_dump(mode="json"),
        timeout=60
    )

    return image_contents.json()

__all__ = ["chat", "get_image", "get_thread", "get_image_contents", "create_thread", "realtime", "transcribe"]
