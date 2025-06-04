"""
Unit tests for CLI module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from airun.cli import cli, run, doctor, config_command, analyze, main
from airun.core.detector import ScriptType
from airun.core.runners import ExecutionResult


class TestCLIBasics:
    """Test basic CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_cli_version(self):
        """Test version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'AIRun version' in result.output

    def test_cli_help(self):
        """Test help output."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'AI-Enhanced Universal Script Runner' in result.output

    def test_run_command_help(self):
        """Test run command help."""
        result = self.runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert 'Execute a script' in result.output


class TestRunCommand:
    """Test the run command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_nonexistent_script(self):
        """Test running non-existent script."""
        result = self.runner.invoke(cli, ['run', '/nonexistent/script.py'])
        assert result.exit_code != 0
        assert 'does not exist' in result.output.lower() or 'path' in result.output.lower()

    @patch('airun.cli.Config.load')
    @patch('airun.cli.ScriptDetector')
    @patch('airun.cli.RunnerFactory.create_runner')
    def test_successful_execution(self, mock_factory, mock_detector, mock_config):
        """Test successful script execution."""
        # Setup mocks
        script_path = self.create_test_script('test.py', 'print("hello")')

        mock_config.return_value = Mock(
            auto_fix=False,
            interactive_mode=False,
            timeout=30,
            runners={}
        )

        mock_detector_instance = Mock()
        mock_detector_instance.detect_type.return_value = ScriptType.PYTHON
        mock_detector.return_value = mock_detector_instance

        mock_runner = Mock()
        mock_runner.validate_executable.return_value = True
        mock_runner.execute.return_value = ExecutionResult(
            exit_code=0,
            stdout="hello\n",
            stderr="",
            execution_time=0.5,
            error_detected=False
        )
        mock_factory.return_value = mock_runner

        result = self.runner.invoke(cli, ['run', script_path])

        assert result.exit_code == 0
        assert 'hello' in result.output
        assert 'Execution completed' in result.output

    @patch('airun.cli.Config.load')
    @patch('airun.cli.ScriptDetector')
    def test_unknown_script_type(self, mock_detector, mock_config):
        """Test handling of unknown script type."""
        script_path = self.create_test_script('unknown.txt', 'some content')

        mock_config.return_value = Mock()
        mock_detector_instance = Mock()
        mock_detector_instance.detect_type.return_value = ScriptType.UNKNOWN
        mock_detector.return_value = mock_detector_instance

        result = self.runner.invoke(cli, ['run', script_path])

        assert result.exit_code == 1
        assert 'Unable to determine script type' in result.output

    @patch('airun.cli.Config.load')
    @patch('airun.cli.ScriptDetector')
    @patch('airun.cli.RunnerFactory.create_runner')
    def test_missing_executable(self, mock_factory, mock_detector, mock_config):
        """Test handling of missing executable."""
        script_path = self.create_test_script('test.py', 'print("hello")')

        mock_config.return_value = Mock(auto_fix=False, runners={})

        mock_detector_instance = Mock()
        mock_detector_instance.detect_type.return_value = ScriptType.PYTHON
        mock_detector.return_value = mock_detector_instance

        mock_runner = Mock()
        mock_runner.validate_executable.return_value = False
        mock_runner.get_executable.return_value = 'python3'
        mock_factory.return_value = mock_runner

        result = self.runner.invoke(cli, ['run', script_path])

        assert result.exit_code == 1
        assert 'not found' in result.output

    def test_forced_language(self):
        """Test forcing specific language."""
        script_path = self.create_test_script('script', 'print("hello")')

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory:

            mock_config.return_value = Mock(auto_fix=False, runners={})

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_runner.execute.return_value = ExecutionResult(
                exit_code=0, stdout="hello\n", stderr="", execution_time=0.5
            )
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', '--lang=python', script_path])

            # Should call factory with PYTHON type
            mock_factory.assert_called_once()
            call_args = mock_factory.call_args[0]
            assert call_args[0] == ScriptType.PYTHON

    def test_dry_run_mode(self):
        """Test dry run functionality."""
        script_path = self.create_test_script('test.py', 'print("hello")')

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.ScriptDetector') as mock_detector, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory, \
             patch('airun.cli.perform_dry_run') as mock_dry_run:

            mock_config.return_value = Mock()
            mock_detector_instance = Mock()
            mock_detector_instance.detect_type.return_value = ScriptType.PYTHON
            mock_detector.return_value = mock_detector_instance

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', '--dry-run', script_path])

            mock_dry_run.assert_called_once()
            assert result.exit_code == 0

    def test_script_arguments_passing(self):
        """Test passing arguments to script."""
        script_path = self.create_test_script('test.py', 'import sys; print(sys.argv)')

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.ScriptDetector') as mock_detector, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory, \
             patch('airun.cli.execute_with_fixing') as mock_execute:

            mock_config.return_value = Mock(auto_fix=False, runners={})

            mock_detector_instance = Mock()
            mock_detector_instance.detect_type.return_value = ScriptType.PYTHON
            mock_detector.return_value = mock_detector_instance

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_factory.return_value = mock_runner

            mock_execute.return_value = ExecutionResult(
                exit_code=0, stdout="", stderr="", execution_time=0.5
            )

            result = self.runner.invoke(cli, ['run', script_path, 'arg1', 'arg2'])

            # Check that arguments were passed
            mock_execute.assert_called_once()
            call_kwargs = mock_execute.call_args.kwargs
            assert call_kwargs['args'] == ['arg1', 'arg2']


class TestDoctorCommand:
    """Test the doctor command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('airun.cli.Config.load')
    @patch('airun.cli.RunnerFactory.validate_all_executables')
    @patch('airun.cli.LLMRouter')
    def test_doctor_success(self, mock_llm_router, mock_validate, mock_config):
        """Test successful doctor diagnosis."""
        mock_config.return_value = Mock(
            llm_providers={'ollama': {}},
            runners={}
        )

        mock_validate.return_value = {
            ScriptType.PYTHON: True,
            ScriptType.SHELL: True,
            ScriptType.NODEJS: False,
            ScriptType.PHP: False,
        }

        mock_llm_instance = Mock()
        mock_llm_instance.get_provider.return_value = Mock()
        mock_llm_router.return_value = mock_llm_instance

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('os.access', return_value=True):

            result = self.runner.invoke(cli, ['doctor'])

            assert result.exit_code == 0
            assert 'System Diagnosis' in result.output
            assert 'Configuration loaded successfully' in result.output

    @patch('airun.cli.Config.load')
    def test_doctor_config_error(self, mock_config):
        """Test doctor with configuration error."""
        mock_config.side_effect = Exception("Config error")

        result = self.runner.invoke(cli, ['doctor'])

        assert result.exit_code == 0  # Doctor doesn't exit with error
        assert 'Configuration error' in result.output


class TestConfigCommand:
    """Test configuration management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('airun.cli.Config.create_default_config')
    @patch('airun.cli.Config.get_default_config_path')
    def test_config_init(self, mock_get_path, mock_create):
        """Test configuration initialization."""
        config_path = Path(self.temp_dir) / 'config.yaml'
        mock_get_path.return_value = config_path

        result = self.runner.invoke(cli, ['config', '--init'])

        assert result.exit_code == 0
        assert 'Created default configuration' in result.output
        mock_create.assert_called_once()

    @patch('airun.cli.Config.load')
    def test_config_show(self, mock_load):
        """Test showing configuration."""
        mock_config = Mock()
        mock_config.to_yaml.return_value = "test: config"
        mock_load.return_value = mock_config

        result = self.runner.invoke(cli, ['config', '--show'])

        assert result.exit_code == 0
        assert 'Current configuration' in result.output
        assert 'test: config' in result.output

    @patch('airun.cli.Config.load')
    def test_config_set(self, mock_load):
        """Test setting configuration values."""
        mock_config = Mock()
        mock_load.return_value = mock_config

        result = self.runner.invoke(cli, ['config', '--set', 'auto_fix=true'])

        assert result.exit_code == 0
        mock_config.set_value.assert_called_with('auto_fix', 'true')
        mock_config.save.assert_called_once()


class TestAnalyzeCommand:
    """Test the analyze command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    @patch('airun.cli.ScriptAnalyzer')
    def test_analyze_text_format(self, mock_analyzer_class):
        """Test script analysis with text format."""
        script_path = self.create_test_script('test.py', 'print("hello")')

        mock_analyzer = Mock()
        mock_analyzer.analyze_script.return_value = {'type': 'python'}
        mock_analyzer.format_analysis_report.return_value = "Analysis report"
        mock_analyzer_class.return_value = mock_analyzer

        result = self.runner.invoke(cli, ['analyze', script_path])

        assert result.exit_code == 0
        assert 'Analysis report' in result.output

    @patch('airun.cli.ScriptAnalyzer')
    def test_analyze_json_format(self, mock_analyzer_class):
        """Test script analysis with JSON format."""
        script_path = self.create_test_script('test.py', 'print("hello")')

        mock_analyzer = Mock()
        mock_analyzer.analyze_script.return_value = {'type': 'python', 'size': 100}
        mock_analyzer_class.return_value = mock_analyzer

        result = self.runner.invoke(cli, ['analyze', '--format=json', script_path])

        assert result.exit_code == 0
        assert '"type": "python"' in result.output

    @patch('airun.cli.ScriptAnalyzer')
    def test_analyze_output_file(self, mock_analyzer_class):
        """Test saving analysis to file."""
        script_path = self.create_test_script('test.py', 'print("hello")')
        output_path = os.path.join(self.temp_dir, 'analysis.txt')

        mock_analyzer = Mock()
        mock_analyzer.analyze_script.return_value = {'type': 'python'}
        mock_analyzer.format_analysis_report.return_value = "Analysis report"
        mock_analyzer_class.return_value = mock_analyzer

        result = self.runner.invoke(cli, ['analyze', '--output', output_path, script_path])

        assert result.exit_code == 0
        assert 'Analysis saved' in result.output

        # Check file was created
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
        assert 'Analysis report' in content


class TestBatchCommand:
    """Test batch execution functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    @patch('airun.cli.BatchExecutor')
    def test_batch_execution(self, mock_executor_class):
        """Test batch script execution."""
        script1 = self.create_test_script('test1.py', 'print("test1")')
        script2 = self.create_test_script('test2.py', 'print("test2")')

        mock_executor = Mock()
        mock_executor.execute_batch.return_value = [
            ExecutionResult(0, "test1\n", "", 0.5),
            ExecutionResult(0, "test2\n", "", 0.7),
        ]
        mock_executor_class.return_value = mock_executor

        result = self.runner.invoke(cli, ['batch', script1, script2])

        assert result.exit_code == 0
        assert 'Executing 2 scripts' in result.output
        assert 'Successful: 2/2' in result.output

    @patch('airun.cli.BatchExecutor')
    def test_batch_with_failures(self, mock_executor_class):
        """Test batch execution with some failures."""
        script1 = self.create_test_script('test1.py', 'print("test1")')
        script2 = self.create_test_script('test2.py', 'exit(1)')

        mock_executor = Mock()
        mock_executor.execute_batch.return_value = [
            ExecutionResult(0, "test1\n", "", 0.5),
            ExecutionResult(1, "", "error", 0.3, error_detected=True),
        ]
        mock_executor_class.return_value = mock_executor

        result = self.runner.invoke(cli, ['batch', script1, script2])

        assert result.exit_code == 1  # Should exit with error
        assert 'Successful: 1/2' in result.output


class TestErrorHandling:
    """Test error handling in CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch('airun.cli.execute_with_fixing') as mock_execute:
            mock_execute.side_effect = KeyboardInterrupt()

            result = self.runner.invoke(cli, ['run', '/nonexistent/script.py'])

            assert result.exit_code == 1
            assert 'Unexpected error' in result.output


class TestMainFunction:
    """Test main entry point function."""

    @patch('airun.cli.cli')
    def test_main_success(self, mock_cli):
        """Test successful main execution."""
        mock_cli.return_value = None

        from airun.cli import main
        main()

        mock_cli.assert_called_once()

    @patch('airun.cli.cli')
    def test_main_keyboard_interrupt(self, mock_cli):
        """Test main with keyboard interrupt."""
        mock_cli.side_effect = KeyboardInterrupt()

        from airun.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 130

    @patch('airun.cli.cli')
    def test_main_click_exception(self, mock_cli):
        """Test main with Click exception."""
        from click import ClickException

        exc = ClickException("Test error")
        exc.exit_code = 2
        mock_cli.side_effect = exc

        from airun.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2


class TestCLIHelpers:
    """Test CLI helper functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    @patch('airun.cli.ScriptDetector')
    @patch('airun.cli.RunnerFactory.create_runner')
    def test_perform_dry_run(self, mock_factory, mock_detector_class):
        """Test perform_dry_run function."""
        from airun.cli import perform_dry_run
        from airun.core.detector import ScriptType

        script_path = self.create_test_script('test.py', 'print("hello")')

        # Setup mocks
        mock_detector = Mock()
        mock_detector.get_file_info.return_value = {
            'filepath': script_path,
            'exists': True,
            'size': 100,
            'extension': '.py',
            'is_executable': False,
            'detected_type': ScriptType.PYTHON,
            'shebang': None,
            'confidence_scores': {ScriptType.PYTHON: 1.0}
        }

        mock_runner = Mock()
        mock_runner.validate_syntax.return_value = None
        mock_runner.validate_executable.return_value = True
        mock_runner.get_executable.return_value = 'python3'
        mock_runner.get_command.return_value = ['python3', script_path]
        mock_factory.return_value = mock_runner

        # Capture output
        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolated_filesystem():
            # This would normally print to stdout
            perform_dry_run(script_path, ScriptType.PYTHON, mock_runner, mock_detector)

        # Verify calls were made
        mock_detector.get_file_info.assert_called_with(script_path)
        mock_runner.validate_syntax.assert_called_with(script_path)
        mock_runner.validate_executable.assert_called_once()

    @patch('airun.cli.AIFixer')
    @patch('airun.cli.ExecutionContext')
    def test_execute_with_fixing_no_fix(self, mock_context_class, mock_fixer_class):
        """Test execute_with_fixing without AI fixing."""
        from airun.cli import execute_with_fixing
        from airun.core.detector import ScriptType

        mock_runner = Mock()
        mock_result = ExecutionResult(0, "success", "", 1.0, False)
        mock_runner.execute.return_value = mock_result

        mock_config = Mock(auto_fix=False)

        result = execute_with_fixing(
            script_path='/path/script.py',
            script_type=ScriptType.PYTHON,
            runner=mock_runner,
            llm_router=None,
            config=mock_config,
            args=[],
            max_retries=3
        )

        assert result == mock_result
        mock_runner.execute.assert_called_once()

    @patch('airun.cli.AIFixer')
    @patch('airun.cli.ExecutionContext')
    def test_execute_with_fixing_success_after_retry(self, mock_context_class, mock_fixer_class):
        """Test execute_with_fixing with successful AI fix."""
        from airun.cli import execute_with_fixing
        from airun.core.detector import ScriptType

        # Setup context mock
        mock_context = Mock()
        mock_context_class.return_value.__enter__.return_value = mock_context

        # First execution fails, second succeeds
        mock_context.execute.side_effect = [
            ExecutionResult(1, "", "error", 1.0, True),  # First attempt fails
            ExecutionResult(0, "success", "", 1.0, False)  # Second attempt succeeds
        ]

        # Setup AI fixer
        mock_fixer = Mock()
        mock_fixer.fix_script_error.return_value = True
        mock_fixer_class.return_value = mock_fixer

        mock_config = Mock(auto_fix=True, interactive_mode=False)
        mock_llm_router = Mock()

        result = execute_with_fixing(
            script_path='/path/script.py',
            script_type=ScriptType.PYTHON,
            runner=Mock(),
            llm_router=mock_llm_router,
            config=mock_config,
            args=[],
            max_retries=3
        )

        assert result.exit_code == 0
        assert result.stdout == "success"
        assert mock_context.execute.call_count == 2
        mock_fixer.fix_script_error.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_script(self, filename: str, content: str) -> str:
        """Create a test script file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_end_to_end_python_execution(self):
        """Test end-to-end Python script execution."""
        script_content = """
print("Hello from Python!")
import sys
print(f"Arguments: {sys.argv[1:]}")
"""
        script_path = self.create_test_script('hello.py', script_content)

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory, \
             patch('airun.cli.ScriptDetector') as mock_detector_class:

            # Setup realistic mocks
            mock_config.return_value = Mock(
                auto_fix=False,
                interactive_mode=False,
                timeout=30,
                runners={'python': {'executable': 'python3', 'flags': ['-u']}}
            )

            mock_detector = Mock()
            mock_detector.detect_type.return_value = ScriptType.PYTHON
            mock_detector_class.return_value = mock_detector

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_runner.execute.return_value = ExecutionResult(
                exit_code=0,
                stdout="Hello from Python!\nArguments: ['arg1', 'arg2']\n",
                stderr="",
                execution_time=0.5,
                error_detected=False
            )
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', script_path, 'arg1', 'arg2'])

            assert result.exit_code == 0
            assert 'Hello from Python!' in result.output
            assert 'Arguments: [\'arg1\', \'arg2\']' in result.output
            assert 'Execution completed in 0.50s' in result.output

    def test_error_execution_with_details(self):
        """Test execution with error and detailed output."""
        script_content = """
import sys
print("This will fail")
sys.exit(1)
"""
        script_path = self.create_test_script('error.py', script_content)

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory, \
             patch('airun.cli.ScriptDetector') as mock_detector_class:

            mock_config.return_value = Mock(
                auto_fix=False,
                runners={'python': {'executable': 'python3'}}
            )

            mock_detector = Mock()
            mock_detector.detect_type.return_value = ScriptType.PYTHON
            mock_detector_class.return_value = mock_detector

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_runner.execute.return_value = ExecutionResult(
                exit_code=1,
                stdout="This will fail\n",
                stderr="",
                execution_time=0.3,
                error_detected=True
            )
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', script_path])

            assert result.exit_code == 1
            assert 'This will fail' in result.output
            assert '❌ Execution completed' in result.output

    def test_verbose_mode(self):
        """Test verbose output mode."""
        script_path = self.create_test_script('test.py', 'print("test")')

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.setup_logging') as mock_logging, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory, \
             patch('airun.cli.ScriptDetector') as mock_detector_class:

            mock_config.return_value = Mock(auto_fix=False, runners={})

            mock_detector = Mock()
            mock_detector.detect_type.return_value = ScriptType.PYTHON
            mock_detector_class.return_value = mock_detector

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_runner.execute.return_value = ExecutionResult(
                exit_code=0, stdout="test\n", stderr="", execution_time=0.1
            )
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', '--verbose', script_path])

            # Verify verbose logging was enabled
            mock_logging.assert_called_with(verbose=True)
            assert result.exit_code == 0


class TestCLIValidation:
    """Test CLI input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_llm_provider_format(self):
        """Test validation of LLM provider format."""
        with patch('airun.cli.validate_llm_provider') as mock_validate:
            mock_validate.return_value = False

            result = self.runner.invoke(cli, [
                'run', '/nonexistent/script.py', '--llm', 'invalid_format'
            ])

            assert result.exit_code == 2  # Click bad parameter
            assert 'Invalid LLM provider format' in result.output

    def test_invalid_script_path(self):
        """Test validation of script path."""
        with patch('airun.cli.validate_script_path') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid script path")

            result = self.runner.invoke(cli, ['run', 'invalid_path'])

            assert result.exit_code == 1
            assert 'Invalid script path' in result.output


class TestCLIConfigIntegration:
    """Test CLI integration with configuration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_custom_config_file(self):
        """Test using custom configuration file."""
        config_content = """
auto_fix: false
timeout: 60
runners:
  python:
    executable: python3
    flags: ["-u"]
"""
        config_path = os.path.join(self.temp_dir, 'custom_config.yaml')
        with open(config_path, 'w') as f:
            f.write(config_content)

        script_path = os.path.join(self.temp_dir, 'test.py')
        with open(script_path, 'w') as f:
            f.write('print("hello")')

        with patch('airun.cli.Config.load') as mock_load:
            mock_config = Mock(auto_fix=False, runners={})
            mock_load.return_value = mock_config

            result = self.runner.invoke(cli, [
                'run', '--config', config_path, script_path
            ])

            # Verify config was loaded with custom path
            mock_load.assert_called_with(config_path)

    def test_cli_option_overrides(self):
        """Test that CLI options override configuration."""
        script_path = os.path.join(self.temp_dir, 'test.py')
        with open(script_path, 'w') as f:
            f.write('print("hello")')

        with patch('airun.cli.Config.load') as mock_config, \
             patch('airun.cli.ScriptDetector') as mock_detector_class, \
             patch('airun.cli.RunnerFactory.create_runner') as mock_factory:

            # Config has auto_fix=True, but CLI passes --no-fix
            config = Mock(auto_fix=True, interactive_mode=False, runners={})
            mock_config.return_value = config

            mock_detector = Mock()
            mock_detector.detect_type.return_value = ScriptType.PYTHON
            mock_detector_class.return_value = mock_detector

            mock_runner = Mock()
            mock_runner.validate_executable.return_value = True
            mock_runner.execute.return_value = ExecutionResult(
                exit_code=0, stdout="hello\n", stderr="", execution_time=0.1
            )
            mock_factory.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', '--no-fix', script_path])

            # Verify auto_fix was overridden to False
            assert config.auto_fix is False
            assert result.exit_code == 0


# Fixtures for testing
@pytest.fixture
def mock_successful_execution():
    """Fixture for successful execution result."""
    return ExecutionResult(
        exit_code=0,
        stdout="Success output\n",
        stderr="",
        execution_time=1.0,
        error_detected=False,
        script_path="/path/to/script.py"
    )


@pytest.fixture
def mock_failed_execution():
    """Fixture for failed execution result."""
    return ExecutionResult(
        exit_code=1,
        stdout="",
        stderr="Error message\n",
        execution_time=0.5,
        error_detected=True,
        script_path="/path/to/script.py"
    )


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return Mock(
        auto_fix=True,
        interactive_mode=False,
        timeout=30,
        default_llm="ollama:codellama",
        runners={
            'python': {'executable': 'python3', 'flags': ['-u']},
            'shell': {'executable': 'bash', 'flags': []},
        },
        llm_providers={
            'ollama': {'base_url': 'http://localhost:11434'}
        }
    )


class TestCLIEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_empty_script_file(self):
        """Test handling of empty script files."""
        with self.runner.isolated_filesystem():
            # Create empty file
            Path('empty.py').touch()

            with patch('airun.cli.Config.load') as mock_config, \
                 patch('airun.cli.ScriptDetector') as mock_detector_class, \
                 patch('airun.cli.RunnerFactory.create_runner') as mock_factory:

                mock_config.return_value = Mock(auto_fix=False, runners={})

                mock_detector = Mock()
                mock_detector.detect_type.return_value = ScriptType.PYTHON
                mock_detector_class.return_value = mock_detector

                mock_runner = Mock()
                mock_runner.validate_executable.return_value = True
                mock_runner.execute.return_value = ExecutionResult(
                    exit_code=0, stdout="", stderr="", execution_time=0.0
                )
                mock_factory.return_value = mock_runner

                result = self.runner.invoke(cli, ['run', 'empty.py'])

                assert result.exit_code == 0

    def test_very_long_script_path(self):
        """Test handling of very long script paths."""
        long_path = '/very/long/path/' + 'a' * 200 + '/script.py'

        result = self.runner.invoke(cli, ['run', long_path])

        # Should handle gracefully (file doesn't exist)
        assert result.exit_code != 0

    def test_special_characters_in_arguments(self):
        """Test handling of special characters in script arguments."""
        with self.runner.isolated_filesystem():
            Path('test.py').write_text('import sys; print(sys.argv)')

            with patch('airun.cli.Config.load') as mock_config, \
                 patch('airun.cli.ScriptDetector') as mock_detector_class, \
                 patch('airun.cli.RunnerFactory.create_runner') as mock_factory:

                mock_config.return_value = Mock(auto_fix=False, runners={})

                mock_detector = Mock()
                mock_detector.detect_type.return_value = ScriptType.PYTHON
                mock_detector_class.return_value = mock_detector

                mock_runner = Mock()
                mock_runner.validate_executable.return_value = True
                mock_runner.execute.return_value = ExecutionResult(
                    exit_code=0, stdout="args processed", stderr="", execution_time=0.1
                )
                mock_factory.return_value = mock_runner

                # Test with special characters
                result = self.runner.invoke(cli, [
                    'run', 'test.py', 'arg with spaces', 'arg!@#$%', 'arg"with"quotes'
                ])

                assert result.exit_code == 0

            assert result.exit_code == 130
            assert 'interrupted' in result.output.lower()

    def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        with patch('airun.cli.Config.load') as mock_config:
            mock_config.side_effect = RuntimeError("Unexpected error")

            result = self.runner.invoke(cli, ['run', '/nonexistent/script.py'])