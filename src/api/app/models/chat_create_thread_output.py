from semantic_kernel.kernel_pydantic import KernelBaseModel
from app.models.content_type_enum import ContentTypeEnum

class ChatCreateThreadOutput(KernelBaseModel):
    thread_id: str

__all__ = ["ChatCreateThreadOutput"]