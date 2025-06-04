"""
Configuration management for AIRun.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """AIRun configuration."""

    # Core settings
    auto_fix: bool = True
    interactive_mode: bool = False
    timeout: int = 300
    max_retries: int = 3

    # LLM settings
    default_llm: str = "ollama:codellama"
    llm_providers: Dict[str, Any] = field(default_factory=dict)

    # Runner settings
    runners: Dict[str, Any] = field(default_factory=dict)

    # Paths and directories
    config_dir: Path = field(default_factory=lambda: Path.home() / ".airun")
    log_dir: Path = field(default_factory=lambda: Path.home() / ".airun" / "logs")
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".airun" / "cache")
    backup_dir: Path = field(default_factory=lambda: Path.home() / ".airun" / "backups")

    # Debugging and logging
    debug: bool = False
    verbose_output: bool = False
    log_level: str = "INFO"

    @classmethod
    def get_default_config_path(cls) -> Path:
        """Get the default configuration file path."""
        return Path.home() / ".airun" / "config.yaml"

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from file.

        Args:
            config_path: Optional path to config file

        Returns:
            Config instance
        """
        if config_path:
            path = Path(config_path)
        else:
            path = cls.get_default_config_path()

        # Create default config if it doesn't exist
        if not path.exists():
            config = cls._get_default_config()
            config.save(path)
            return config

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            return cls._from_dict(data)

        except Exception as e:
            raise ValueError(f"Failed to load configuration from {path}: {e}")

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()

        # Update basic fields
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Ensure directories are Path objects
        for dir_attr in ['config_dir', 'log_dir', 'cache_dir', 'backup_dir']:
            if hasattr(config, dir_attr):
                current_value = getattr(config, dir_attr)
                if isinstance(current_value, str):
                    setattr(config, dir_attr, Path(current_value))

        return config

    @classmethod
    def _get_default_config(cls) -> "Config":
        """Get default configuration."""
        config = cls()

        # Default LLM providers
        config.llm_providers = {
            'ollama': {
                'base_url': 'http://localhost:11434',
                'models': {
                    'python': 'codellama:7b',
                    'shell': 'codellama:7b',
                    'nodejs': 'codellama:7b',
                    'php': 'codellama:7b'
                }
            }
        }

        # Default runners
        config.runners = {
            'python': {
                'executable': 'python3',
                'flags': ['-u']
            },
            'shell': {
                'executable': 'bash',
                'flags': []
            },
            'nodejs': {
                'executable': 'node',
                'flags': []
            },
            'php': {
                'executable': 'php',
                'flags': []
            }
        }

        return config

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to file.

        Args:
            config_path: Optional path to save config
        """
        if config_path is None:
            config_path = self.get_default_config_path()

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary
        data = self._to_dict()

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {config_path}: {e}")

    def _to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        data = {}

        # Include all non-private attributes
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, Path):
                    data[key] = str(value)
                else:
                    data[key] = value

        return data

    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        return yaml.dump(self._to_dict(), default_flow_style=False, indent=2)

    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'runners.python.executable')
            value: Value to set
        """
        keys = key.split('.')
        obj = self

        # Navigate to the parent object
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            elif isinstance(obj, dict) and k in obj:
                obj = obj[k]
            else:
                raise KeyError(f"Configuration key '{k}' not found")

        # Set the final value
        final_key = keys[-1]
        if hasattr(obj, final_key):
            # Convert string boolean values
            if isinstance(value, str) and value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif isinstance(value, str) and value.isdigit():
                value = int(value)

            setattr(obj, final_key, value)
        elif isinstance(obj, dict):
            obj[final_key] = value
        else:
            raise KeyError(f"Configuration key '{final_key}' not found")

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'runners.python.executable')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        obj = self

        try:
            for k in keys:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                elif isinstance(obj, dict) and k in obj:
                    obj = obj[k]
                else:
                    return default

            return obj

        except (AttributeError, KeyError, TypeError):
            return default

    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        directories = [
            self.config_dir,
            self.log_dir,
            self.cache_dir,
            self.backup_dir
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Failed to create directory {directory}: {e}")

    @classmethod
    def create_default_config(cls, force: bool = False) -> "Config":
        """
        Create default configuration file.

        Args:
            force: Overwrite existing config if True

        Returns:
            Created config instance
        """
        config_path = cls.get_default_config_path()

        if config_path.exists() and not force:
            raise FileExistsError(f"Configuration file already exists: {config_path}")

        config = cls._get_default_config()
        config.ensure_directories()
        config.save(config_path)

        return config

    def validate(self) -> None:
        """Validate configuration settings."""
        errors = []

        # Validate timeout
        if self.timeout <= 0:
            errors.append("timeout must be positive")

        # Validate max_retries
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")

        # Validate LLM provider format
        if self.default_llm and ':' not in self.default_llm:
            errors.append("default_llm must be in format 'provider:model'")

        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            errors.append(f"log_level must be one of: {valid_levels}")

        # Validate required runner executables
        for runner_name, runner_config in self.runners.items():
            if not isinstance(runner_config, dict):
                errors.append(f"runner '{runner_name}' config must be a dictionary")
                continue

            if 'executable' not in runner_config:
                errors.append(f"runner '{runner_name}' missing 'executable' key")

        if errors:
            raise ValueError("Configuration validation failed: " + "; ".join(errors))

    def get_runner_config(self, runner_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific runner.

        Args:
            runner_type: Type of runner (python, shell, nodejs, php)

        Returns:
            Runner configuration dictionary
        """
        return self.runners.get(runner_type, {})

    def get_llm_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific LLM provider.

        Args:
            provider_name: Name of the LLM provider

        Returns:
            LLM provider configuration dictionary
        """
        return self.llm_providers.get(provider_name, {})

    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        env_mappings = {
            'AIRUN_AUTO_FIX': ('auto_fix', bool),
            'AIRUN_INTERACTIVE': ('interactive_mode', bool),
            'AIRUN_TIMEOUT': ('timeout', int),
            'AIRUN_MAX_RETRIES': ('max_retries', int),
            'AIRUN_DEFAULT_LLM': ('default_llm', str),
            'AIRUN_DEBUG': ('debug', bool),
            'AIRUN_LOG_LEVEL': ('log_level', str),
        }

        for env_var, (attr_name, attr_type) in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                try:
                    if attr_type == bool:
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif attr_type == int:
                        value = int(env_value)
                    else:
                        value = env_value

                    setattr(self, attr_name, value)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid environment variable {env_var}={env_value}: {e}")

    def merge_with_project_config(self, project_dir: Path) -> "Config":
        """
        Merge with project-specific configuration.

        Args:
            project_dir: Project directory to look for .airunner.yaml

        Returns:
            New config instance with merged settings
        """
        project_config_path = project_dir / ".airunner.yaml"

        if not project_config_path.exists():
            return self

        try:
            with open(project_config_path, 'r', encoding='utf-8') as f:
                project_data = yaml.safe_load(f) or {}

            # Create a copy of current config
            merged_data = self._to_dict()

            # Deep merge project configuration
            merged_data = self._deep_merge(merged_data, project_data)

            return self._from_dict(merged_data)

        except Exception as e:
            raise ValueError(f"Failed to load project config from {project_config_path}: {e}")

    @staticmethod
    def _deep_merge(base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base_dict: Base dictionary
            override_dict: Dictionary to merge into base

        Returns:
            Merged dictionary
        """
        result = base_dict.copy()

        for key, value in override_dict.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config(auto_fix={self.auto_fix}, default_llm='{self.default_llm}')"


class ConfigManager:
    """Manages configuration loading and caching."""

    _instance: Optional[Config] = None
    _config_path: Optional[Path] = None

    @classmethod
    def get_config(cls, config_path: Optional[str] = None,
                   force_reload: bool = False) -> Config:
        """
        Get cached configuration instance.

        Args:
            config_path: Optional path to config file
            force_reload: Force reload from file

        Returns:
            Config instance
        """
        current_path = Path(config_path) if config_path else Config.get_default_config_path()

        if (cls._instance is None or
            cls._config_path != current_path or
            force_reload):

            cls._instance = Config.load(config_path)
            cls._config_path = current_path

            # Apply environment overrides
            cls._instance.update_from_env()

            # Validate configuration
            cls._instance.validate()

            # Ensure directories exist
            cls._instance.ensure_directories()

        return cls._instance

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached configuration."""
        cls._instance = None
        cls._config_path = None


# Convenience functions
def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration (convenience function)."""
    return Config.load(config_path)


def get_config(config_path: Optional[str] = None) -> Config:
    """Get cached configuration (convenience function)."""
    return ConfigManager.get_config(config_path)


def create_default_config(force: bool = False) -> Config:
    """Create default configuration (convenience function)."""
    return Config.create_default_config(force)


# Configuration validation helpers
def validate_llm_provider(provider_string: str) -> bool:
    """
    Validate LLM provider string format.

    Args:
        provider_string: Provider string (e.g., 'ollama:codellama')

    Returns:
        True if valid format
    """
    if not provider_string or not isinstance(provider_string, str):
        return False

    parts = provider_string.split(':')
    if len(parts) != 2:
        return False

    provider, model = parts
    if not provider.strip() or not model.strip():
        return False

    # Check for valid provider names
    valid_providers = ['ollama', 'openai', 'claude', 'anthropic']
    if provider.lower() not in valid_providers:
        return False

    return True


def get_config_template() -> str:
    """
    Get a YAML template for configuration file.

    Returns:
        YAML configuration template
    """
    template = """
# AIRun Configuration File
# See https://docs.airun.dev/configuration for full documentation

# Core Settings
auto_fix: true                    # Enable automatic error fixing
interactive_mode: false           # Prompt before applying fixes
timeout: 300                      # Script execution timeout (seconds)
max_retries: 3                    # Maximum fix attempts

# Default LLM Provider
default_llm: "ollama:codellama"   # Format: provider:model

# LLM Providers Configuration
llm_providers:
  ollama:
    base_url: "http://localhost:11434"
    models:
      python: "codellama:7b"
      shell: "codellama:7b"
      nodejs: "codellama:7b"
      php: "codellama:7b"
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
  
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"

# Script Runners Configuration
runners:
  python:
    executable: "python3"
    flags: ["-u"]                 # Unbuffered output
  
  shell:
    executable: "bash"
    flags: []
  
  nodejs:
    executable: "node"
    flags: []
  
  php:
    executable: "php"
    flags: []

# Directories (relative to ~/.airun/)
log_dir: "logs"
cache_dir: "cache"
backup_dir: "backups"

# Debugging and Logging
debug: false
verbose_output: false
log_level: "INFO"                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
"""
    return template.strip()