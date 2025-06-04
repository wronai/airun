"""
Validation utilities for AIRun.
"""
import os
import re
from pathlib import Path
from typing import Optional


def validate_script_path(script_path: str) -> str:
    """
    Validate and normalize script path.

    Args:
        script_path: Path to script file

    Returns:
        Normalized absolute path

    Raises:
        ValueError: If path is invalid or file doesn't exist
    """
    if not script_path or not isinstance(script_path, str):
        raise ValueError("Script path must be a non-empty string")

    path = Path(script_path).resolve()

    if not path.exists():
        raise ValueError(f"Script file does not exist: {script_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {script_path}")

    if not os.access(path, os.R_OK):
        raise ValueError(f"Script file is not readable: {script_path}")

    return str(path)


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

    # Check basic format: provider:model
    if ':' not in provider_string:
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

    # Basic model name validation (alphanumeric, dash, underscore)
    if not re.match(r'^[a-zA-Z0-9_-]+$', model):
        return False

    return True


def validate_timeout(timeout: int) -> bool:
    """
    Validate timeout value.

    Args:
        timeout: Timeout in seconds

    Returns:
        True if valid
    """
    return isinstance(timeout, int) and 1 <= timeout <= 3600  # 1 second to 1 hour


def validate_max_retries(max_retries: int) -> bool:
    """
    Validate max retries value.

    Args:
        max_retries: Maximum number of retries

    Returns:
        True if valid
    """
    return isinstance(max_retries, int) and 0 <= max_retries <= 10


def validate_confidence_threshold(threshold: float) -> bool:
    """
    Validate confidence threshold.

    Args:
        threshold: Confidence threshold (0.0 to 1.0)

    Returns:
        True if valid
    """
    return isinstance(threshold, (int, float)) and 0.0 <= threshold <= 1.0


def validate_file_extension(filepath: str, allowed_extensions: list) -> bool:
    """
    Validate file extension against allowed list.

    Args:
        filepath: Path to file
        allowed_extensions: List of allowed extensions (e.g., ['.py', '.js'])

    Returns:
        True if extension is allowed
    """
    if not filepath:
        return False

    extension = Path(filepath).suffix.lower()
    return extension in [ext.lower() for ext in allowed_extensions]


def validate_executable_name(executable: str) -> bool:
    """
    Validate executable name format.

    Args:
        executable: Name or path of executable

    Returns:
        True if valid format
    """
    if not executable or not isinstance(executable, str):
        return False

    # Allow alphanumeric, dash, underscore, dot, slash (for paths)
    if not re.match(r'^[a-zA-Z0-9_./:-]+, executable):
        return False

    # Must not be empty after stripping
    return len(executable.strip()) > 0


def validate_port(port: int) -> bool:
    """
    Validate port number.

    Args:
        port: Port number

    Returns:
        True if valid port
    """
    return isinstance(port, int) and 1 <= port <= 65535


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string

    Returns:
        True if valid URL format
    """
    if not url or not isinstance(url, str):
        return False

    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)*'  # domain
        r'[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?'  # host
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+), re.IGNORECASE  # path
    )

    return bool(url_pattern.match(url))


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key string

    Returns:
        True if valid format
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # API keys are typically 20+ characters, alphanumeric with some special chars
    if len(api_key.strip()) < 10:
        return False

    # Check for reasonable API key pattern
    if not re.match(r'^[a-zA-Z0-9_.-]+, api_key):
        return False

    return True


def validate_log_level(log_level: str) -> bool:
    """
    Validate logging level.

    Args:
        log_level: Log level string

    Returns:
        True if valid log level
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    return log_level and log_level.upper() in valid_levels


def validate_script_arguments(args: list) -> bool:
    """
    Validate script arguments list.

    Args:
        args: List of arguments

    Returns:
        True if valid
    """
    if not isinstance(args, list):
        return False

    # All arguments should be strings
    return all(isinstance(arg, str) for arg in args)


def validate_environment_variables(env_vars: dict) -> bool:
    """
    Validate environment variables dictionary.

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        True if valid
    """
    if not isinstance(env_vars, dict):
        return False

    # Keys and values should be strings
    for key, value in env_vars.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return False

        # Environment variable names should be valid
        if not re.match(r'^[A-Z_][A-Z0-9_]*, key):
            return False

    return True


def validate_directory_path(directory_path: str) -> bool:
    """
    Validate directory path.

    Args:
        directory_path: Path to directory

    Returns:
        True if valid directory path
    """
    if not directory_path or not isinstance(directory_path, str):
        return False

    try:
        path = Path(directory_path)
        # Path should be absolute or relative but valid
        return True
    except Exception:
        return False


def validate_file_permissions(filepath: str, permission: str = 'r') -> bool:
    """
    Validate file permissions.

    Args:
        filepath: Path to file
        permission: Permission to check ('r', 'w', 'x')

    Returns:
        True if file has required permission
    """
    if not os.path.exists(filepath):
        return False

    if permission == 'r':
        return os.access(filepath, os.R_OK)
    elif permission == 'w':
        return os.access(filepath, os.W_OK)
    elif permission == 'x':
        return os.access(filepath, os.X_OK)
    else:
        return False


def validate_json_string(json_string: str) -> bool:
    """
    Validate JSON string format.

    Args:
        json_string: JSON string to validate

    Returns:
        True if valid JSON
    """
    if not json_string or not isinstance(json_string, str):
        return False

    try:
        import json
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def validate_yaml_string(yaml_string: str) -> bool:
    """
    Validate YAML string format.

    Args:
        yaml_string: YAML string to validate

    Returns:
        True if valid YAML
    """
    if not yaml_string or not isinstance(yaml_string, str):
        return False

    try:
        import yaml
        yaml.safe_load(yaml_string)
        return True
    except yaml.YAMLError:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        return "untitled"

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"

    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    return sanitized


def validate_model_name(model_name: str) -> bool:
    """
    Validate AI model name format.

    Args:
        model_name: Model name

    Returns:
        True if valid model name
    """
    if not model_name or not isinstance(model_name, str):
        return False

    # Model names can contain letters, numbers, hyphens, underscores, dots, colons
    if not re.match(r'^[a-zA-Z0-9_.-]+(?::[a-zA-Z0-9_.-]+)*, model_name):
        return False

    # Must not be empty after stripping
    return len(model_name.strip()) > 0


def validate_batch_size(batch_size: int) -> bool:
    """
    Validate batch size for batch operations.

    Args:
        batch_size: Number of items in batch

    Returns:
        True if valid batch size
    """
    return isinstance(batch_size, int) and 1 <= batch_size <= 1000


def validate_config_section(config_dict: dict, required_keys: list) -> tuple[bool, list]:
    """
    Validate configuration section has required keys.

    Args:
        config_dict: Configuration dictionary
        required_keys: List of required keys

    Returns:
        Tuple of (is_valid, missing_keys)
    """
    if not isinstance(config_dict, dict):
        return False, required_keys

    missing_keys = [key for key in required_keys if key not in config_dict]
    return len(missing_keys) == 0, missing_keys


def validate_semantic_version(version: str) -> bool:
    """
    Validate semantic version string (e.g., 1.2.3).

    Args:
        version: Version string

    Returns:
        True if valid semantic version
    """
    if not version or not isinstance(version, str):
        return False

    # Semantic version pattern: major.minor.patch with optional pre-release/build
    semver_pattern = re.compile(
        r'^(?P<major>0|[1-9]\d*)'
        r'\.(?P<minor>0|[1-9]\d*)'
        r'\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?
    )

    return bool(semver_pattern.match(version))


# Validation decorator for functions
def validate_types(**type_checks):
    """
    Decorator to validate function argument types.

    Args:
        **type_checks: Mapping of argument names to expected types

    Usage:
        @validate_types(script_path=str, timeout=int)
        def my_function(script_path, timeout):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import inspect

            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate types
            for param_name, expected_type in type_checks.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )

            return func(*args, **kwargs)
        return wrapper
    return decorator