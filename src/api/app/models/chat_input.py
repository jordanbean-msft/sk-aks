from typing import List
from pydantic import BaseModel
from semantic_kernel.contents.chat_history import ChatHistory

class ChatInput(BaseModel):
    thread_id: str
    aks_cluster_name: str
    content: str 

__all__ = ["ChatInput"]
