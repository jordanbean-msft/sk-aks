from semantic_kernel.kernel_pydantic import KernelBaseModel
from models.content_type_enum import ContentTypeEnum

class ChatOutput(KernelBaseModel):
    content_type: ContentTypeEnum
    content: str
    thread_id: str

def deserialize_chat_output(chat_output):
    if isinstance(chat_output, dict):
        return ChatOutput(
            content_type=ContentTypeEnum(chat_output["content_type"]),
            content=chat_output["content"],
            thread_id=chat_output["thread_id"],
        )
    raise TypeError("Invalid type for deserialization")

__all__ = ["ChatOutput", "deserialize_chat_output"]