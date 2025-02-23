from typing import List
from pydantic import BaseModel

class ChatGetThreadInput(BaseModel):
    thread_id: str

__all__ = ["ChatGetThreadInput"]
