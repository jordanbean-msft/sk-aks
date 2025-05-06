from pydantic import BaseModel
from semantic_kernel.contents.chat_history import ChatHistory

class ChatRealtimeInput(BaseModel):
    thread_id: str

__all__ = ["ChatRealtimeInput"]
