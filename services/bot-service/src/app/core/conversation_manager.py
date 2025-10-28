from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from ..core.mongo_orchestrator_client import MongoOrchestratorClient

class ConversationManager:
    """
    Stores sessions and messages via the MongoOrchestratorClient.
    Collections: sessions, messages
    """
    def __init__(self, db_client: MongoOrchestratorClient):
        self.db = db_client
        self.sessions_col = "sessions"
        self.messages_col = "messages"

    async def create_session_if_missing(self, session_id: str, user_id: str, metadata: Optional[dict] = None):
        now = datetime.now(timezone.utc)
        existing = await self.db.find_one(self.sessions_col, {"session_id": session_id})
        if not existing:
            doc = {
                "session_id": session_id,
                "user_id": user_id,
                "metadata": metadata or {},
                "createdAt": now.isoformat(),
                "updatedAt": now.isoformat(),
            }
            await self.db.insert_one(self.sessions_col, doc)
        else:
            await self.db.update_one(self.sessions_col, {"session_id": session_id}, {"$set": {"updatedAt": now.isoformat()}})

    async def append_message(self, session_id: str, user_id: str, role: str, text: str):
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        await self.db.insert_one(self.messages_col, doc)

    async def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        res = await self.db.find(self.messages_col, {"session_id": session_id}, sort={"createdAt": 1}, limit=limit)
        return res