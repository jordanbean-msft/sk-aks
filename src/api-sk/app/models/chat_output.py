from pydantic import BaseModel

class ChatOutput(BaseModel):
    thread_id: str
    messages: list[str]

__all__ = ["ChatOutput"]
