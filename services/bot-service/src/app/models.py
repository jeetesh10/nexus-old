# filepath: /workspaces/nexus/services/bot-service/src/app/models.py
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    goal_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response_message: str
