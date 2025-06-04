"""
Script execution runners for AIRun.
"""
import subprocess
import time
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from .detector import ScriptType


@dataclass
class ExecutionResult:
    """Result of script execution."""
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    error_detected: bool = False
    script_path: str = ""
    script_type: Optional[ScriptType] = None


class ExecutionError(Exception):
    """Custom exception for execution errors."""

    def __init__(self, message: str, result: ExecutionResult):
        super().__init__(message)
        self.result = result


class BaseRunner(ABC):
    """Abstract base class for script runners."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the runner.

        Args:
            config: Runner configuration
        """
        self.config = config
        self.timeout = config.get('timeout', 300)  # 5 minutes default

    @abstractmethod
    def get_command(self, script_path: str, args: List[str] = None) -> List[str]:
        """
        Build command to execute the script.

        Args:
            script_path: Path to the script
            args: Additional arguments

        Returns:
            Command as list of strings
        """
        pass

    def execute(self, script_path: str, args: List[str] = None,
                cwd: Optional[str] = None) -> ExecutionResult:
        """
        Execute the script.

        Args:
            script_path: Path to the script
            args: Additional arguments
            cwd: Working directory

        Returns:
            Execution result
        """
        cmd = self.get_command(script_path, args)
        return self._run_subprocess(cmd, cwd, script_path)

    def _run_subprocess(self, cmd: List[str], cwd: Optional[str] = None,
                       script_path: str = "") -> ExecutionResult:
        """
        Execute command using subprocess.

        Args:
            cmd: Command to execute
            cwd: Working directory
            script_path: Original script path for logging

        Returns:
            Execution result
        """
        start_time = time.time()

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.get('env_vars', {}))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or os.path.dirname(script_path) if script_path else None,
                timeout=self.timeout,
                env=env
            )

            execution_time = time.time() - start_time

            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                error_detected=result.returncode != 0,
                script_path=script_path
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Execution timeout exceeded ({self.timeout}s)",
                execution_time=execution_time,
                error_detected=True,
                script_path=script_path
            )
        except FileNotFoundError as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=-2,
                stdout="",
                stderr=f"Command not found: {e}",
                execution_time=execution_time,
                error_detected=True,
                script_path=script_path
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=-3,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time,
                error_detected=True,
                script_path=script_path
            )

    def validate_executable(self) -> bool:
        """Check if the required executable is available."""
        executable = self.get_executable()
        try:
            result = subprocess.run(
                [executable, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    @abstractmethod
    def get_executable(self) -> str:
        """Get the main executable for this runner."""
        pass


class PythonRunner(BaseRunner):
    """Python script runner."""

    def get_executable(self) -> str:
        """Get Python executable."""
        return self.config.get('python', {}).get('executable', 'python3')

    def get_command(self, script_path: str, args: List[str] = None) -> List[str]:
        """Build Python execution command."""
        executable = self.get_executable()
        flags = self.config.get('python', {}).get('flags', ['-u'])

        cmd = [executable] + flags + [script_path]
        if args:
            cmd.extend(args)

        return cmd

    def validate_syntax(self, script_path: str) -> Optional[str]:
        """
        Validate Python syntax without executing.

        Args:
            script_path: Path to Python script

        Returns:
            Error message if syntax is invalid, None otherwise
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                source = f.read()

            compile(source, script_path, 'exec')
            return None

        except SyntaxError as e:
            return f"Syntax error in {script_path}:{e.lineno}: {e.msg}"
        except Exception as e:
            return f"Error reading {script_path}: {e}"


class ShellRunner(BaseRunner):
    """Shell script runner."""

    def get_executable(self) -> str:
        """Get shell executable."""
        return self.config.get('shell', {}).get('executable', 'bash')

    def get_command(self, script_path: str, args: List[str] = None) -> List[str]:
        """Build shell execution command."""
        executable = self.get_executable()
        flags = self.config.get('shell', {}).get('flags', [])

        cmd = [executable] + flags + [script_path]
        if args:
            cmd.extend(args)

        return cmd

    def validate_syntax(self, script_path: str) -> Optional[str]:
        """
        Validate shell script syntax.

        Args:
            script_path: Path to shell script

        Returns:
            Error message if syntax is invalid, None otherwise
        """
        try:
            result = subprocess.run(
                [self.get_executable(), '-n', script_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return f"Syntax error in {script_path}: {result.stderr}"

            return None

        except Exception as e:
            return f"Error validating {script_path}: {e}"


class NodeJSRunner(BaseRunner):
    """Node.js script runner."""

    def get_executable(self) -> str:
        """Get Node.js executable."""
        return self.config.get('nodejs', {}).get('executable', 'node')

    def get_command(self, script_path: str, args: List[str] = None) -> List[str]:
        """Build Node.js execution command."""
        executable = self.get_executable()
        flags = self.config.get('nodejs', {}).get('flags', [])

        cmd = [executable] + flags + [script_path]
        if args:
            cmd.extend(args)

        return cmd

    def validate_syntax(self, script_path: str) -> Optional[str]:
        """
        Validate JavaScript syntax.

        Args:
            script_path: Path to JavaScript file

        Returns:
            Error message if syntax is invalid, None otherwise
        """
        try:
            result = subprocess.run(
                [self.get_executable(), '--check', script_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return f"Syntax error in {script_path}: {result.stderr}"

            return None

        except Exception as e:
            return f"Error validating {script_path}: {e}"


class PHPRunner(BaseRunner):
    """PHP script runner."""

    def get_executable(self) -> str:
        """Get PHP executable."""
        return self.config.get('php', {}).get('executable', 'php')

    def get_command(self, script_path: str, args: List[str] = None) -> List[str]:
        """Build PHP execution command."""
        executable = self.get_executable()
        flags = self.config.get('php', {}).get('flags', [])

        cmd = [executable] + flags + [script_path]
        if args:
            cmd.extend(args)

        return cmd

    def validate_syntax(self, script_path: str) -> Optional[str]:
        """
        Validate PHP syntax.

        Args:
            script_path: Path to PHP file

        Returns:
            Error message if syntax is invalid, None otherwise
        """
        try:
            result = subprocess.run(
                [self.get_executable(), '-l', script_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return f"Syntax error in {script_path}: {result.stderr}"

            return None

        except Exception as e:
            return f"Error validating {script_path}: {e}"


class RunnerFactory:
    """Factory for creating script runners."""

    _RUNNERS = {
        ScriptType.PYTHON: PythonRunner,
        ScriptType.SHELL: ShellRunner,
        ScriptType.NODEJS: NodeJSRunner,
        ScriptType.PHP: PHPRunner,
    }

    @classmethod
    def create_runner(cls, script_type: ScriptType, config: Dict[str, Any]) -> BaseRunner:
        """
        Create a runner for the given script type.

        Args:
            script_type: Type of script
            config: Runner configuration

        Returns:
            Appropriate runner instance

        Raises:
            ValueError: If script type is not supported
        """
        if script_type not in cls._RUNNERS:
            raise ValueError(f"Unsupported script type: {script_type}")

        runner_class = cls._RUNNERS[script_type]
        return runner_class(config)

    @classmethod
    def get_supported_types(cls) -> List[ScriptType]:
        """Get list of supported script types."""
        return list(cls._RUNNERS.keys())

    @classmethod
    def validate_all_executables(cls, config: Dict[str, Any]) -> Dict[ScriptType, bool]:
        """
        Validate that all required executables are available.

        Args:
            config: Runner configuration

        Returns:
            Dictionary mapping script types to availability status
        """
        results = {}

        for script_type in cls._RUNNERS:
            try:
                runner = cls.create_runner(script_type, config)
                results[script_type] = runner.validate_executable()
            except Exception:
                results[script_type] = False

        return results


class ExecutionContext:
    """Context manager for script execution with cleanup."""

    def __init__(self, script_path: str, runner: BaseRunner,
                 backup_original: bool = True):
        """
        Initialize execution context.

        Args:
            script_path: Path to script
            runner: Runner to use
            backup_original: Whether to backup original file
        """
        self.script_path = Path(script_path)
        self.runner = runner
        self.backup_original = backup_original
        self.backup_path: Optional[Path] = None
        self.original_content: Optional[str] = None

    def __enter__(self):
        """Enter context and create backup if needed."""
        if self.backup_original and self.script_path.exists():
            try:
                self.original_content = self.script_path.read_text(encoding='utf-8')
                timestamp = int(time.time())
                self.backup_path = self.script_path.with_suffix(
                    f'.backup.{timestamp}{self.script_path.suffix}'
                )
                self.backup_path.write_text(self.original_content, encoding='utf-8')
            except Exception:
                # Continue without backup if it fails
                pass

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup if needed."""
        # Restore original content if execution failed and we have a backup
        if exc_type and self.original_content:
            try:
                self.script_path.write_text(self.original_content, encoding='utf-8')
            except Exception:
                pass

    def execute(self, args: List[str] = None) -> ExecutionResult:
        """Execute script within this context."""
        return self.runner.execute(str(self.script_path), args)

    def restore_from_backup(self) -> bool:
        """
        Restore original file from backup.

        Returns:
            True if restoration was successful
        """
        if self.original_content:
            try:
                self.script_path.write_text(self.original_content, encoding='utf-8')
                return True
            except Exception:
                return False
        return False