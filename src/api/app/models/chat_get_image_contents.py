from typing import List
from pydantic import BaseModel

class ChatGetImageContents(BaseModel):
    thread_id: str

__all__ = ["ChatGetImageContents"]
