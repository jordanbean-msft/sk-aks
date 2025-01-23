from pydantic import BaseModel

class ChatInput(BaseModel):
    agent_id: str
    thread_id: str
    aks_access_token: str
    aks_cluster_name: str
    content: str

__all__ = ["ChatInput"]
