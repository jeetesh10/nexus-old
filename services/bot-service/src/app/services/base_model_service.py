# filepath: /workspaces/nexus/services/bot-service/src/app/services/base_model_service.py
from abc import ABC, abstractmethod

class BaseModelService(ABC):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """Synchronously invoke model and return text."""
        raise NotImplementedError
