"""
AIRun - AI-Enhanced Universal Script Runner
"""
__version__ = "0.1.0"
__author__ = "AIRun Team"
__email__ = "contact@airun.dev"
__description__ = "AI-Enhanced Universal Script Runner with automatic error fixing"

from .core.detector import ScriptDetector, ScriptType
from .core.runners import ExecutionResult, RunnerFactory
from .core.config import Config

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "ScriptDetector",
    "ScriptType",
    "ExecutionResult",
    "RunnerFactory",
    "Config",
]