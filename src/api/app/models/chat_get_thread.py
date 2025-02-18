from typing import List
from pydantic import BaseModel

class ChatGetThreadInput(BaseModel):
    agent_id: str
    thread_id: str

__all__ = ["ChatGetThreadInput"]
