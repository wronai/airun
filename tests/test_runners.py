"""
Unit tests for script runners module.
"""
import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from airun.core.runners import (
    ExecutionResult, ExecutionError, BaseRunner, PythonRunner,
    ShellRunner, NodeJSRunner, PHPRunner, RunnerFactory,
    ExecutionContext
)
from airun.core.detector import ScriptType


class TestExecutionResult:
    """Test cases for ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test ExecutionResult creation and attributes."""
        result = ExecutionResult(
            exit_code=0,
            stdout="Hello World",
            stderr="",
            execution_time=1.5,
            error_detected=False,
            script_path="/path/to/script.py"
        )

        assert result.exit_code == 0
        assert result.stdout == "Hello World"
        assert result.stderr == ""
        assert result.execution_time == 1.5
        assert result.error_detected is False
        assert result.script_path == "/path/to/script.py"

    def test_execution_result_defaults(self):
        """Test ExecutionResult with default values."""
        result = ExecutionResult(
            exit_code=1,
            stdout="",
            stderr="Error occurred",
            execution_time=0.5
        )

        assert result.error_detected is False  # Default value
        assert result.script_path == ""  # Default value


class TestExecutionError:
    """Test cases for ExecutionError exception."""

    def test_execution_error_creation(self):
        """Test ExecutionError creation with result."""
        result = ExecutionResult(1, "", "Error", 1.0, True)
        error = ExecutionError("Test error", result)

        assert str(error) == "Test error"
        assert error.result == result


class MockRunner(BaseRunner):
    """Mock runner for testing BaseRunner functionality."""

    def get_command(self, script_path: str, args=None):
        return ['echo', 'test']

    def get_executable(self):
        return 'echo'


class TestBaseRunner:
    """Test cases for BaseRunner abstract class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'timeout': 30,
            'env_vars': {'TEST_VAR': 'test_value'}
        }
        self.runner = MockRunner(self.config)

    def test_base_runner_initialization(self):
        """Test BaseRunner initialization."""
        assert self.runner.config == self.config
        assert self.runner.timeout == 30

    def test_base_runner_default_timeout(self):
        """Test BaseRunner with default timeout."""
        runner = MockRunner({})
        assert runner.timeout == 300  # Default 5 minutes

    @patch('subprocess.run')
    def test_successful_execution(self, mock_run):
        """Test successful script execution."""
        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.runner.execute('/path/to/script')

        assert result.exit_code == 0
        assert result.stdout == "Success"
        assert result.stderr == ""
        assert result.error_detected is False
        assert result.execution_time > 0

    @patch('subprocess.run')
    def test_failed_execution(self, mock_run):
        """Test failed script execution."""
        # Mock failed subprocess execution
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error occurred"
        mock_run.return_value = mock_result

        result = self.runner.execute('/path/to/script')

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == "Error occurred"
        assert result.error_detected is True

    @patch('subprocess.run')
    def test_timeout_handling(self, mock_run):
        """Test execution timeout handling."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(['cmd'], 30)

        result = self.runner.execute('/path/to/script')

        assert result.exit_code == -1
        assert "timeout" in result.stderr.lower()
        assert result.error_detected is True

    @patch('subprocess.run')
    def test_file_not_found_handling(self, mock_run):
        """Test handling of missing executable."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = self.runner.execute('/path/to/script')

        assert result.exit_code == -2
        assert "not found" in result.stderr.lower()
        assert result.error_detected is True

    @patch('subprocess.run')
    def test_environment_variables(self, mock_run):
        """Test that environment variables are passed correctly."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        self.runner.execute('/path/to/script')

        # Check that subprocess.run was called with custom environment
        call_args = mock_run.call_args
        env = call_args.kwargs.get('env')
        assert env is not None
        assert env.get('TEST_VAR') == 'test_value'


class TestPythonRunner:
    """Test cases for PythonRunner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'python': {
                'executable': 'python3',
                'flags': ['-u', '-W', 'ignore']
            }
        }
        self.runner = PythonRunner(self.config)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_executable(self):
        """Test getting Python executable."""
        assert self.runner.get_executable() == 'python3'

    def test_get_executable_default(self):
        """Test default Python executable."""
        runner = PythonRunner({})
        assert runner.get_executable() == 'python3'

    def test_get_command(self):
        """Test building Python command."""
        cmd = self.runner.get_command('/path/script.py', ['arg1', 'arg2'])
        expected = ['python3', '-u', '-W', 'ignore', '/path/script.py', 'arg1', 'arg2']
        assert cmd == expected

    def test_get_command_no_args(self):
        """Test building Python command without arguments."""
        cmd = self.runner.get_command('/path/script.py')
        expected = ['python3', '-u', '-W', 'ignore', '/path/script.py']
        assert cmd == expected

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test Python script."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_validate_syntax_valid(self):
        """Test syntax validation with valid Python code."""
        valid_content = """
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""
        filepath = self.create_test_script('valid.py', valid_content)
        error = self.runner.validate_syntax(filepath)
        assert error is None

    def test_validate_syntax_invalid(self):
        """Test syntax validation with invalid Python code."""
        invalid_content = """
def hello():
    print("Hello, World!"  # Missing closing parenthesis

if __name__ == "__main__":
    hello()
"""
        filepath = self.create_test_script('invalid.py', invalid_content)
        error = self.runner.validate_syntax(filepath)
        assert error is not None
        assert "syntax error" in error.lower()

    @patch('subprocess.run')
    def test_validate_executable(self, mock_run):
        """Test executable validation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert self.runner.validate_executable() is True

        # Test failure case
        mock_result.returncode = 1
        assert self.runner.validate_executable() is False


class TestShellRunner:
    """Test cases for ShellRunner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'shell': {
                'executable': 'bash',
                'flags': ['-e']
            }
        }
        self.runner = ShellRunner(self.config)

    def test_get_executable(self):
        """Test getting shell executable."""
        assert self.runner.get_executable() == 'bash'

    def test_get_command(self):
        """Test building shell command."""
        cmd = self.runner.get_command('/path/script.sh', ['arg1'])
        expected = ['bash', '-e', '/path/script.sh', 'arg1']
        assert cmd == expected

    @patch('subprocess.run')
    def test_validate_syntax(self, mock_run):
        """Test shell syntax validation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        error = self.runner.validate_syntax('/path/script.sh')
        assert error is None

        # Check that bash -n was called
        call_args = mock_run.call_args[0][0]
        assert 'bash' in call_args
        assert '-n' in call_args


class TestNodeJSRunner:
    """Test cases for NodeJSRunner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'nodejs': {
                'executable': 'node',
                'flags': ['--experimental-modules']
            }
        }
        self.runner = NodeJSRunner(self.config)

    def test_get_executable(self):
        """Test getting Node.js executable."""
        assert self.runner.get_executable() == 'node'

    def test_get_command(self):
        """Test building Node.js command."""
        cmd = self.runner.get_command('/path/app.js')
        expected = ['node', '--experimental-modules', '/path/app.js']
        assert cmd == expected

    @patch('subprocess.run')
    def test_validate_syntax(self, mock_run):
        """Test JavaScript syntax validation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        error = self.runner.validate_syntax('/path/app.js')
        assert error is None

        # Check that node --check was called
        call_args = mock_run.call_args[0][0]
        assert 'node' in call_args
        assert '--check' in call_args


class TestPHPRunner:
    """Test cases for PHPRunner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'php': {
                'executable': 'php',
                'flags': ['-f']
            }
        }
        self.runner = PHPRunner(self.config)

    def test_get_executable(self):
        """Test getting PHP executable."""
        assert self.runner.get_executable() == 'php'

    def test_get_command(self):
        """Test building PHP command."""
        cmd = self.runner.get_command('/path/index.php')
        expected = ['php', '-f', '/path/index.php']
        assert cmd == expected

    @patch('subprocess.run')
    def test_validate_syntax(self, mock_run):
        """Test PHP syntax validation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        error = self.runner.validate_syntax('/path/index.php')
        assert error is None

        # Check that php -l was called
        call_args = mock_run.call_args[0][0]
        assert 'php' in call_args
        assert '-l' in call_args


class TestRunnerFactory:
    """Test cases for RunnerFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {'timeout': 60}

    def test_create_python_runner(self):
        """Test creating Python runner."""
        runner = RunnerFactory.create_runner(ScriptType.PYTHON, self.config)
        assert isinstance(runner, PythonRunner)
        assert runner.config == self.config

    def test_create_shell_runner(self):
        """Test creating shell runner."""
        runner = RunnerFactory.create_runner(ScriptType.SHELL, self.config)
        assert isinstance(runner, ShellRunner)

    def test_create_nodejs_runner(self):
        """Test creating Node.js runner."""
        runner = RunnerFactory.create_runner(ScriptType.NODEJS, self.config)
        assert isinstance(runner, NodeJSRunner)

    def test_create_php_runner(self):
        """Test creating PHP runner."""
        runner = RunnerFactory.create_runner(ScriptType.PHP, self.config)
        assert isinstance(runner, PHPRunner)

    def test_create_unsupported_runner(self):
        """Test creating runner for unsupported type."""
        with pytest.raises(ValueError, match="Unsupported script type"):
            RunnerFactory.create_runner(ScriptType.UNKNOWN, self.config)

    def test_get_supported_types(self):
        """Test getting supported script types."""
        types = RunnerFactory.get_supported_types()
        expected = [ScriptType.PYTHON, ScriptType.SHELL, ScriptType.NODEJS, ScriptType.PHP]
        assert set(types) == set(expected)

    @patch('airun.core.runners.PythonRunner.validate_executable')
    @patch('airun.core.runners.ShellRunner.validate_executable')
    def test_validate_all_executables(self, mock_shell, mock_python):
        """Test validating all executables."""
        mock_python.return_value = True
        mock_shell.return_value = False

        results = RunnerFactory.validate_all_executables(self.config)

        assert results[ScriptType.PYTHON] is True
        assert results[ScriptType.SHELL] is False
        assert ScriptType.NODEJS in results
        assert ScriptType.PHP in results


class TestExecutionContext:
    """Test cases for ExecutionContext."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {}

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, 'test_script.py')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_context_manager_backup(self):
        """Test context manager creates backup."""
        original_content = "print('original')"
        script_path = self.create_test_script(original_content)
        runner = MockRunner(self.config)

        with ExecutionContext(script_path, runner, backup_original=True) as ctx:
            assert ctx.original_content == original_content
            assert ctx.backup_path is not None
            assert ctx.backup_path.exists()

    def test_context_manager_no_backup(self):
        """Test context manager without backup."""
        script_path = self.create_test_script("print('test')")
        runner = MockRunner(self.config)

        with ExecutionContext(script_path, runner, backup_original=False) as ctx:
            assert ctx.original_content is None
            assert ctx.backup_path is None

    @patch('subprocess.run')
    def test_execute_within_context(self, mock_run):
        """Test executing script within context."""
        script_path = self.create_test_script("print('test')")
        runner = MockRunner(self.config)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with ExecutionContext(script_path, runner) as ctx:
            result = ctx.execute(['arg1'])
            assert result.exit_code == 0
            assert result.stdout == "test"

    def test_restore_from_backup(self):
        """Test restoring original content from backup."""
        original_content = "print('original')"
        script_path = self.create_test_script(original_content)
        runner = MockRunner(self.config)

        with ExecutionContext(script_path, runner, backup_original=True) as ctx:
            # Modify the file
            with open(script_path, 'w') as f:
                f.write("print('modified')")

            # Restore from backup
            success = ctx.restore_from_backup()
            assert success is True

            # Check content was restored
            with open(script_path, 'r') as f:
                content = f.read()
            assert content == original_content


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration."""
    return {
        'timeout': 30,
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


class TestIntegrationScenarios:
    """Integration test scenarios for runners."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_script(self, filename: str, content: str) -> str:
        """Create a test script."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_python_script_execution(self, mock_config