from typing import List
from pydantic import BaseModel

class ChatGetImageInput(BaseModel):
    file_id: str

__all__ = ["ChatGetImageInput"]
