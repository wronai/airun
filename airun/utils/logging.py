"""
Logging utilities for AIRun.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno',
                          'pathname', 'filename', 'module', 'exc_info',
                          'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'getMessage'):
                log_entry[key] = value

        return json.dumps(log_entry)


class FileRotatingHandler(logging.handlers.RotatingFileHandler):
    """Custom rotating file handler with automatic directory creation."""

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None):
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, mode, maxBytes, backupCount, encoding)


def setup_logging(
    level: str = "INFO",
    verbose: bool = False,
    log_file: Optional[str] = None,
    json_format: bool = False,
    colored_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration for AIRun.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: Enable verbose logging
        log_file: Optional log file path
        json_format: Use JSON format for file logging
        colored_output: Use colored output for console
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Override level if verbose is enabled
    if verbose:
        numeric_level = logging.DEBUG

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if colored_output and sys.stdout.isatty():
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = FileRotatingHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file

        if json_format:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_execution(logger: logging.Logger, script_path: str, args: list = None) -> None:
    """
    Log script execution details.

    Args:
        logger: Logger instance
        script_path: Path to script being executed
        args: Script arguments
    """
    logger.info(
        "Executing script",
        extra={
            'script_path': script_path,
            'script_args': args or [],
            'action': 'execute_script'
        }
    )


def log_error_fix_attempt(logger: logging.Logger, script_path: str,
                         provider: str, confidence: float) -> None:
    """
    Log AI error fix attempt.

    Args:
        logger: Logger instance
        script_path: Path to script being fixed
        provider: LLM provider used
        confidence: Fix confidence score
    """
    logger.info(
        "Attempting AI error fix",
        extra={
            'script_path': script_path,
            'llm_provider': provider,
            'fix_confidence': confidence,
            'action': 'ai_fix_attempt'
        }
    )


def log_performance_metrics(logger: logging.Logger, operation: str,
                          duration: float, **metrics) -> None:
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **metrics: Additional metrics to log
    """
    logger.info(
        f"Performance metrics for {operation}",
        extra={
            'operation': operation,
            'duration_seconds': duration,
            'action': 'performance_metrics',
            **metrics
        }
    )


def log_system_info(logger: logging.Logger) -> None:
    """
    Log system information for debugging.

    Args:
        logger: Logger instance
    """
    import platform
    import sys
    import os

    logger.debug(
        "System information",
        extra={
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'memory_gb': round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**3), 2) if hasattr(os, 'sysconf') else 'unknown',
            'working_directory': os.getcwd(),
            'action': 'system_info'
        }
    )


class LogContext:
    """Context manager for adding context to log messages."""

    def __init__(self, logger: logging.Logger, **context):
        """
        Initialize log context.

        Args:
            logger: Logger instance
            **context: Context variables to add to log records
        """
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def setup_execution_logging(script_path: str, log_dir: Optional[str] = None) -> str:
    """
    Setup logging for script execution with automatic log file naming.

    Args:
        script_path: Path to script being executed
        log_dir: Directory for log files

    Returns:
        Path to created log file
    """
    if log_dir is None:
        log_dir = Path.home() / ".airun" / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log filename based on script name and timestamp
    script_name = Path(script_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{script_name}_{timestamp}.log"
    log_file_path = log_dir / log_filename

    # Setup logging with the execution log file
    setup_logging(
        level="DEBUG",
        log_file=str(log_file_path),
        json_format=True
    )

    return str(log_file_path)


class PerformanceLogger:
    """Logger for tracking performance metrics."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.

        Args:
            logger: Logger instance to use
        """
        self.logger = logger
        self.start_times: Dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """
        Start timing an operation.

        Args:
            operation: Operation name
        """
        import time
        self.start_times[operation] = time.time()
        self.logger.debug(f"Started timing: {operation}")

    def end_timer(self, operation: str, **extra_metrics) -> float:
        """
        End timing an operation and log the duration.

        Args:
            operation: Operation name
            **extra_metrics: Additional metrics to log

        Returns:
            Duration in seconds
        """
        import time

        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return 0.0

        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]

        log_performance_metrics(
            self.logger,
            operation,
            duration,
            **extra_metrics
        )

        return duration

    def time_operation(self, operation: str):
        """
        Context manager for timing operations.

        Args:
            operation: Operation name

        Usage:
            with perf_logger.time_operation("my_operation"):
                # code to time
                pass
        """
        return TimedOperation(self, operation)


class TimedOperation:
    """Context manager for timing operations."""

    def __init__(self, perf_logger: PerformanceLogger, operation: str):
        """
        Initialize timed operation.

        Args:
            perf_logger: Performance logger instance
            operation: Operation name
        """
        self.perf_logger = perf_logger
        self.operation = operation

    def __enter__(self):
        self.perf_logger.start_timer(self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.perf_logger.end_timer(self.operation)


def configure_third_party_loggers() -> None:
    """Configure third-party library loggers to reduce noise."""
    # Reduce verbosity of common third-party libraries
    noisy_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3',
        'httpx',
        'openai',
        'anthropic',
    ]

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_log_file_path(log_dir: Optional[str] = None) -> str:
    """
    Get the default log file path.

    Args:
        log_dir: Optional log directory

    Returns:
        Default log file path
    """
    if log_dir is None:
        log_dir = Path.home() / ".airun" / "logs"

    log_dir = Path(log_dir)
    return str(log_dir / "airun.log")


# Initialize third-party logger configuration
configure_third_party_loggers()