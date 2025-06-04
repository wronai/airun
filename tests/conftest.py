"""
Pytest configuration and shared fixtures for AIRun tests.
"""
import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

from airun.core.config import Config
from airun.core.detector import ScriptType
from airun.core.runners import ExecutionResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_scripts(temp_dir):
    """Create sample script files for testing."""
    scripts = {}

    # Python script
    python_content = '''#!/usr/bin/env python3
import sys
print("Hello from Python!")
print("Arguments:", sys.argv[1:])
'''
    python_path = os.path.join(temp_dir, 'test.py')
    with open(python_path, 'w') as f:
        f.write(python_content)
    scripts['python'] = python_path

    # Shell script
    shell_content = '''#!/bin/bash
echo "Hello from Bash!"
echo "First arg: $1"
'''
    shell_path = os.path.join(temp_dir, 'test.sh')
    with open(shell_path, 'w') as f:
        f.write(shell_content)
    os.chmod(shell_path, 0o755)
    scripts['shell'] = shell_path

    # Node.js script
    node_content = '''#!/usr/bin/env node
console.log("Hello from Node.js!");
console.log("Arguments:", process.argv.slice(2));
'''
    node_path = os.path.join(temp_dir, 'test.js')
    with open(node_path, 'w') as f:
        f.write(node_content)
    scripts['nodejs'] = node_path

    # PHP script
    php_content = '''#!/usr/bin/env php
<?php
echo "Hello from PHP!\n";
echo "Arguments: " . implode(", ", array_slice($argv, 1)) . "\n";
?>
'''
    php_path = os.path.join(temp_dir, 'test.php')
    with open(php_path, 'w') as f:
        f.write(php_content)
    scripts['php'] = php_path

    return scripts


@pytest.fixture
def broken_scripts(temp_dir):
    """Create broken script files for testing error handling."""
    scripts = {}

    # Broken Python script (syntax error)
    python_content = '''#!/usr/bin/env python3
import sys
print("Hello from Python!"  # Missing closing parenthesis
print("This will cause a syntax error")
'''
    python_path = os.path.join(temp_dir, 'broken.py')
    with open(python_path, 'w') as f:
        f.write(python_content)
    scripts['python'] = python_path

    # Broken shell script (command not found)
    shell_content = '''#!/bin/bash
echo "Starting script..."
nonexistent_command_that_should_fail
echo "This won't be reached"
'''
    shell_path = os.path.join(temp_dir, 'broken.sh')
    with open(shell_path, 'w') as f:
        f.write(shell_content)
    os.chmod(shell_path, 0o755)
    scripts['shell'] = shell_path

    # Broken Node.js script (reference error)
    node_content = '''#!/usr/bin/env node
console.log("Starting Node.js script...");
console.log(undefinedVariable);  // This will cause ReferenceError
console.log("This won't be reached");
'''
    node_path = os.path.join(temp_dir, 'broken.js')
    with open(node_path, 'w') as f:
        f.write(node_content)
    scripts['nodejs'] = node_path

    # Broken PHP script (parse error)
    php_content = '''#!/usr/bin/env php
<?php
echo "Starting PHP script...\n";
echo "Missing semicolon here"  // This will cause parse error
echo "This won't be reached\n";
?>
'''
    php_path = os.path.join(temp_dir, 'broken.php')
    with open(php_path, 'w') as f:
        f.write(php_content)
    scripts['php'] = php_path

    return scripts


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.auto_fix = True
    config.interactive_mode = False
    config.timeout = 30
    config.max_retries = 3
    config.default_llm = "ollama:codellama"
    config.min_confidence_threshold = 0.5
    config.backup_enabled = True

    config.runners = {
        'python': {'executable': 'python3', 'flags': ['-u']},
        'shell': {'executable': 'bash', 'flags': []},
        'nodejs': {'executable': 'node', 'flags': []},
        'php': {'executable': 'php', 'flags': []},
    }

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

    return config


@pytest.fixture
def mock_execution_result():
    """Mock execution result for testing."""

    def _create_result(exit_code=0, stdout="", stderr="", execution_time=1.0, error_detected=None):
        if error_detected is None:
            error_detected = exit_code != 0

        return ExecutionResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            error_detected=error_detected
        )

    return _create_result


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    from airun.core.llm_router import CodeFix

    provider = Mock()
    provider.name = "mock_provider"
    provider.is_available.return_value = True

    # Default successful fix
    provider.generate_fix.return_value = CodeFix(
        fixed_code="print('Fixed code')",
        explanation="Fixed the syntax error",
        confidence=0.9,
        changes_made=["Added missing parenthesis"]
    )

    return provider


@pytest.fixture
def mock_llm_router(mock_llm_provider):
    """Mock LLM router for testing."""
    router = Mock()
    router.get_provider.return_value = mock_llm_provider
    router.fix_error.return_value = mock_llm_provider.generate_fix.return_value
    router.get_available_providers.return_value = ["mock_provider"]

    return router


@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample configuration file."""
    config_content = """
auto_fix: true
interactive_mode: false
timeout: 300
max_retries: 3
default_llm: "ollama:codellama"

llm_providers:
  ollama:
    base_url: "http://localhost:11434"
    models:
      python: "codellama:7b"
      shell: "codellama:7b"
      nodejs: "codellama:7b"
      php: "codellama:7b"

runners:
  python:
    executable: "python3"
    flags: ["-u"]
  shell:
    executable: "bash"
    flags: []
  nodejs:
    executable: "node"
    flags: []
  php:
    executable: "php"
    flags: []
"""

    config_path = os.path.join(temp_dir, 'test_config.yaml')
    with open(config_path, 'w') as f:
        f.write(config_content)

    return config_path


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    # Disable actual LLM calls during tests
    monkeypatch.setenv("AIRUN_TEST_MODE", "1")

    # Set test-specific configuration
    monkeypatch.setenv("AIRUN_AUTO_FIX", "false")
    monkeypatch.setenv("AIRUN_DEBUG", "true")


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Add handler to airun loggers
    airun_logger = logging.getLogger('airun')
    airun_logger.addHandler(handler)
    airun_logger.setLevel(logging.DEBUG)

    yield log_capture

    # Clean up
    airun_logger.removeHandler(handler)


@pytest.fixture
def isolated_filesystem():
    """Create an isolated filesystem for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            os.chdir(original_cwd)


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (longer execution time)"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )
    config.addinivalue_line(
        "markers", "llm: marks tests that require LLM services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark LLM tests
        if "llm" in item.name.lower() or "ollama" in item.name.lower():
            item.add_marker(pytest.mark.llm)

        # Mark network tests
        if any(keyword in item.name.lower() for keyword in ["api", "http", "network"]):
            item.add_marker(pytest.mark.network)


# Helper functions for tests
def create_test_script(directory: str, filename: str, content: str, executable: bool = False) -> str:
    """Helper function to create test scripts."""
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    if executable:
        os.chmod(filepath, 0o755)

    return filepath


def assert_file_exists(filepath: str, message: str = None):
    """Helper assertion for file existence."""
    if not os.path.exists(filepath):
        msg = message or f"File does not exist: {filepath}"
        pytest.fail(msg)


def assert_file_content_equals(filepath: str, expected_content: str):
    """Helper assertion for file content."""
    assert_file_exists(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        actual_content = f.read()
    assert actual_content == expected_content, f"File content mismatch in {filepath}"


def assert_command_succeeds(command: list, cwd: str = None):
    """Helper assertion for command execution."""
    import subprocess
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            pytest.fail(f"Command failed: {' '.join(command)}\nstderr: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        pytest.fail(f"Command timed out: {' '.join(command)}")
    except Exception as e:
        pytest.fail(f"Command execution failed: {e}")