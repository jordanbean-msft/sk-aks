from semantic_kernel.kernel_pydantic import KernelBaseModel
from app.models.content_type_enum import ContentTypeEnum

class ChatOutput(KernelBaseModel):
    content_type: ContentTypeEnum
    content: str
    thread_id: str

def serialize_chat_output(chat_output):
    if isinstance(chat_output, ChatOutput):
        return {
            "content_type": chat_output.content_type.value,
            "content": chat_output.content,
            "thread_id": chat_output.thread_id,
        }
    raise TypeError

__all__ = ["ChatOutput", "serialize_chat_output"]