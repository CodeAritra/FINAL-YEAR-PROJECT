"""
Root configuration forwarder.
Preserves backward compatibility for all imports from `config`.
"""

from config.settings import settings, Settings, BASE_DIR
from config.model_config import ModelExecutionMode, ResearchSecurityMode

__all__ = ["settings", "Settings", "BASE_DIR", "ModelExecutionMode", "ResearchSecurityMode"]
