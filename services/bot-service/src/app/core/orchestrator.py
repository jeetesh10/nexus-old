# filepath: /workspaces/nexus/services/bot-service/src/app/core/orchestrator.py
import asyncio
from typing import Optional
from ..core.llm_manager import AsyncLLMManager
from ..core.conversation_manager import ConversationManager

class Orchestrator:
    def __init__(self, llm_manager: AsyncLLMManager, convo_manager: ConversationManager):
        self.llm = llm_manager
        self.convo = convo_manager

    async def process_request(self, user_id: str, session_id: str, message: str, goal_id: Optional[str] = None) -> dict:
        """
        Async orchestrator flow:
         - persist user message (async)
         - select model (async)
         - run synchronous model.invoke in a thread
         - persist assistant response (async)
        """
        await self.convo.create_session_if_missing(session_id, user_id)
        await self.convo.append_message(session_id, user_id, "user", message)

        model_service = await self.llm.get_model_service(None)
        # run blocking model call in a thread
        result = await asyncio.to_thread(model_service.invoke, message)

        await self.convo.append_message(session_id, user_id, "assistant", result)

        return {"session_id": session_id, "response_message": result}
