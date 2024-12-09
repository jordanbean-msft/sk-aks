from pydantic import BaseModel


class ChatOutput(BaseModel):
    thread_id: str
    message: str

__all__ = ["ChatOutput"]
