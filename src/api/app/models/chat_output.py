from semantic_kernel.kernel_pydantic import KernelBaseModel
from app.models.content_type_enum import ContentTypeEnum

class ChatOutput(KernelBaseModel):
    content_type: ContentTypeEnum
    content: str
    thread_id: str

__all__ = ["ChatOutput"]