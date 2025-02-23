from typing import List
from pydantic import BaseModel
from semantic_kernel.contents.chat_history import ChatHistory

class ChatInput(BaseModel):
    #agent_id: str
    thread_id: str
    #aks_access_token: str
    aks_cluster_name: str
    content: ChatHistory

__all__ = ["ChatInput"]
