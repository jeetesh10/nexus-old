# filepath: services/bot-service/src/app/core/config.py
import os
from typing import Optional, Any

# Try pydantic v2 settings package first, fallback to pydantic.BaseSettings, otherwise use env fallback.
BaseSettingsImpl = None
try:
    from pydantic_settings import BaseSettings as BaseSettingsImpl  # type: ignore
except Exception:
    try:
        from pydantic import BaseSettings as BaseSettingsImpl  # type: ignore
    except Exception:
        BaseSettingsImpl = None

class Settings:
    """Lightweight settings wrapper. If a pydantic BaseSettings implementation
    is available at runtime (pydantic-settings or pydantic.BaseSettings), its
    values are used; otherwise values are read from environment variables.
    This keeps typing simple for static analysis while still supporting
    pydantic-based configuration in environments where it's installed.
    """

    def __init__(self) -> None:
        # defaults stored as private attrs to avoid flagged constant reassignments
        self._mongodb_orchestrator_url = os.getenv("MONGODB_ORCHESTRATOR_URL", "http://127.0.0.1:8001")
        self._env = os.getenv("ENV", "dev")

        # if BaseSettingsImpl is available, prefer its values (if set)
        try:
            if BaseSettingsImpl is not None:
                base = BaseSettingsImpl()
                base_any: Any = base
                # use getattr with defaults to avoid attribute errors
                self._mongodb_orchestrator_url = getattr(base_any, "MONGODB_ORCHESTRATOR_URL", self._mongodb_orchestrator_url)
                self._env = getattr(base_any, "ENV", self._env)
        except Exception:
            # non-fatal: fall back to environment values
            pass

    @property
    def MONGODB_ORCHESTRATOR_URL(self) -> str:
        return self._mongodb_orchestrator_url

    @property
    def ENV(self) -> str:
        return self._env


# singleton instance used by the app
settings = Settings()
