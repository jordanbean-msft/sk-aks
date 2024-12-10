from pydantic import BaseModel


class ChatInput(BaseModel):
    thread_id: str
    message: str

__all__ = ["ChatInput"]
