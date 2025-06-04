"""
AIRun Core Module
Core functionality for script execution and AI-powered error fixing.
"""

from .detector import ScriptDetector, ScriptType
from .runners import (
    ExecutionResult,
    ExecutionError,
    BaseRunner,
    PythonRunner,
    ShellRunner,
    NodeJSRunner,
    PHPRunner,
    RunnerFactory,
    ExecutionContext
)
from .config import Config, ConfigManager, load_config, get_config
from .llm_router import LLMRouter, LLMProvider
from .ai_fixer import AIFixer, ErrorContext, CodeFix

__all__ = [
    # Script Detection
    "ScriptDetector",
    "ScriptType",

    # Script Execution
    "ExecutionResult",
    "ExecutionError",
    "BaseRunner",
    "PythonRunner",
    "ShellRunner",
    "NodeJSRunner",
    "PHPRunner",
    "RunnerFactory",
    "ExecutionContext",

    # Configuration
    "Config",
    "ConfigManager",
    "load_config",
    "get_config",

    # AI Integration
    "LLMRouter",
    "LLMProvider",
    "AIFixer",
    "ErrorContext",
    "CodeFix",
]