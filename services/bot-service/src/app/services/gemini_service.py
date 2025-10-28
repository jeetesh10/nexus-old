# filepath: /workspaces/nexus/services/bot-service/src/app/services/gemini_service.py
from .base_model_service import BaseModelService

class GeminiService(BaseModelService):
    def invoke(self, prompt: str, **kwargs) -> str:
        # TODO: replace with google-generativeai SDK calls
        return f"[gemini simulated] response to: {prompt}"
