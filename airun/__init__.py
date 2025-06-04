"""
AIRun - AI-Enhanced Universal Script Runner
"""
__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.detector import ScriptDetector
from .core.runners import ExecutionResult
from .core.llm_router import LLMRouter
from .core.config import Config

__all__ = [
    "ScriptDetector",
    "ExecutionResult",
    "LLMRouter",
    "Config",
]