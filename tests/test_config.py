"""
Unit tests for configuration module.
"""
import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from airun.core.config import (
    Config, ConfigManager, load_config, get_config,
    create_default_config, validate_llm_provider, get_config_template
)


class TestConfig:
    """Test cases for Config class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clear config manager cache
        ConfigManager.clear_cache()

    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()

        assert config.auto_fix is True
        assert config.interactive_mode is False
        assert config.timeout == 300
        assert config.max_retries == 3
        assert config.default_llm == "ollama:codellama"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert isinstance(config.config_dir, Path)
        assert isinstance(config.llm_providers, dict)
        assert isinstance(config.runners, dict)

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        data = config._to_dict()

        assert isinstance(data, dict)
        assert 'auto_fix' in data
        assert 'timeout' in data
        assert 'llm_providers' in data

        # Path objects should be converted to strings
        assert isinstance(data['config_dir'], str)

    def test_config_to_yaml(self):
        """Test converting config to YAML."""
        config = Config()
        yaml_str = config.to_yaml()

        assert isinstance(yaml_str, str)
        assert 'auto_fix:' in yaml_str
        assert 'timeout:' in yaml_str

        # Should be valid YAML
        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict)

    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        # Create config with custom values
        config = Config()
        config.auto_fix = False
        config.timeout = 600
        config.default_llm = "openai:gpt-4"

        # Save to file
        config.save(self.config_path)
        assert self.config_path.exists()

        # Load from file
        loaded_config = Config.load(str(self.config_path))

        assert loaded_config.auto_fix is False
        assert loaded_config.timeout == 600
        assert loaded_config.default_llm == "openai:gpt-4"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            'auto_fix': False,
            'timeout': 600,
            'default_llm': 'custom:model',
            'config_dir': '/custom/path',
            'llm_providers': {
                'custom': {'api_key': 'test'}
            }
        }

        config = Config._from_dict(data)

        assert config.auto_fix is False
        assert config.timeout == 600
        assert config.default_llm == 'custom:model'
        assert isinstance(config.config_dir, Path)
        assert str(config.config_dir) == '/custom/path'
        assert 'custom' in config.llm_providers

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = Config._get_default_config()

        assert isinstance(config.llm_providers, dict)
        assert 'ollama' in config.llm_providers
        assert isinstance(config.runners, dict)
        assert 'python' in config.runners
        assert 'shell' in config.runners
        assert 'nodejs' in config.runners
        assert 'php' in config.runners

    def test_config_load_nonexistent_creates_default(self):
        """Test that loading non-existent config creates default."""
        nonexistent_path = self.temp_dir / "nonexistent.yaml"

        with patch.object(Config, 'get_default_config_path', return_value=nonexistent_path):
            config = Config.load()

        assert nonexistent_path.exists()
        assert config.auto_fix is True  # Default value

    def test_config_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        # Create invalid YAML file
        self.config_path.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Failed to load configuration"):
            Config.load(str(self.config_path))

    def test_set_value_simple(self):
        """Test setting simple configuration values."""
        config = Config()

        config.set_value('auto_fix', 'false')
        assert config.auto_fix is False

        config.set_value('timeout', '600')
        assert config.timeout == 600

        config.set_value('default_llm', 'custom:model')
        assert config.default_llm == 'custom:model'

    def test_set_value_nested(self):
        """Test setting nested configuration values."""
        config = Config()
        config.runners = {'python': {'executable': 'python3'}}

        config.set_value('runners.python.executable', 'python3.11')
        assert config.runners['python']['executable'] == 'python3.11'

    def test_set_value_invalid_key(self):
        """Test setting invalid configuration key."""
        config = Config()

        with pytest.raises(KeyError):
            config.set_value('invalid.key', 'value')

    def test_get_value_simple(self):
        """Test getting simple configuration values."""
        config = Config()
        config.auto_fix = True
        config.timeout = 300

        assert config.get_value('auto_fix') is True
        assert config.get_value('timeout') == 300
        assert config.get_value('nonexistent', 'default') == 'default'

    def test_get_value_nested(self):
        """Test getting nested configuration values."""
        config = Config()
        config.runners = {'python': {'executable': 'python3'}}

        assert config.get_value('runners.python.executable') == 'python3'
        assert config.get_value('runners.python.nonexistent', 'default') == 'default'

    def test_get_runner_config(self):
        """Test getting runner-specific configuration."""
        config = Config()
        config.runners = {
            'python': {'executable': 'python3', 'flags': ['-u']},
            'shell': {'executable': 'bash'}
        }

        python_config = config.get_runner_config('python')
        assert python_config['executable'] == 'python3'
        assert python_config['flags'] == ['-u']

        nonexistent_config = config.get_runner_config('nonexistent')
        assert nonexistent_config == {}

    def test_get_llm_config(self):
        """Test getting LLM provider configuration."""
        config = Config()
        config.llm_providers = {
            'ollama': {'base_url': 'http://localhost:11434'},
            'openai': {'api_key': 'test-key'}
        }

        ollama_config = config.get_llm_config('ollama')
        assert ollama_config['base_url'] == 'http://localhost:11434'

        nonexistent_config = config.get_llm_config('nonexistent')
        assert nonexistent_config == {}


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_success(self):
        """Test successful validation."""
        config = Config()
        config.timeout = 300
        config.max_retries = 3
        config.default_llm = "ollama:codellama"
        config.log_level = "INFO"
        config.runners = {
            'python': {'executable': 'python3'}
        }

        # Should not raise exception
        config.validate()

    def test_validate_invalid_timeout(self):
        """Test validation with invalid timeout."""
        config = Config()
        config.timeout = -1

        with pytest.raises(ValueError, match="timeout must be positive"):
            config.validate()

    def test_validate_invalid_max_retries(self):
        """Test validation with invalid max_retries."""
        config = Config()
        config.max_retries = -1

        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            config.validate()

    def test_validate_invalid_llm_format(self):
        """Test validation with invalid LLM format."""
        config = Config()
        config.default_llm = "invalid_format"

        with pytest.raises(ValueError, match="default_llm must be in format"):
            config.validate()

    def test_validate_invalid_log_level(self):
        """Test validation with invalid log level."""
        config = Config()
        config.log_level = "INVALID"

        with pytest.raises(ValueError, match="log_level must be one of"):
            config.validate()

    def test_validate_missing_runner_executable(self):
        """Test validation with missing runner executable."""
        config = Config()
        config.runners = {
            'python': {}  # Missing 'executable' key
        }

        with pytest.raises(ValueError, match="missing 'executable' key"):
            config.validate()

    def test_validate_invalid_runner_config(self):
        """Test validation with invalid runner config."""
        config = Config()
        config.runners = {
            'python': 'not_a_dict'  # Should be dictionary
        }

        with pytest.raises(ValueError, match="config must be a dictionary"):
            config.validate()


class TestConfigEnvironment:
    """Test environment variable integration."""

    def test_update_from_env(self):
        """Test updating config from environment variables."""
        config = Config()

        with patch.dict(os.environ, {
            'AIRUN_AUTO_FIX': 'false',
            'AIRUN_TIMEOUT': '600',
            'AIRUN_DEFAULT_LLM': 'openai:gpt-4',
            'AIRUN_DEBUG': 'true'
        }):
            config.update_from_env()

        assert config.auto_fix is False
        assert config.timeout == 600
        assert config.default_llm == 'openai:gpt-4'
        assert config.debug is True

    def test_update_from_env_bool_variations(self):
        """Test boolean environment variable variations."""
        config = Config()

        # Test various boolean representations
        bool_values = ['true', '1', 'yes', 'on', 'TRUE', 'True']
        for value in bool_values:
            with patch.dict(os.environ, {'AIRUN_AUTO_FIX': value}):
                config.update_from_env()
                assert config.auto_fix is True

        bool_false_values = ['false', '0', 'no', 'off', 'FALSE', 'False']
        for value in bool_false_values:
            with patch.dict(os.environ, {'AIRUN_AUTO_FIX': value}):
                config.update_from_env()
                assert config.auto_fix is False

    def test_update_from_env_invalid_int(self):
        """Test invalid integer environment variable."""
        config = Config()

        with patch.dict(os.environ, {'AIRUN_TIMEOUT': 'not_a_number'}):
            with pytest.raises(ValueError, match="Invalid environment variable"):
                config.update_from_env()


class TestConfigProjectMerging:
    """Test project-specific configuration merging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_merge_with_project_config(self):
        """Test merging with project configuration."""
        # Create base config
        base_config = Config()
        base_config.auto_fix = True
        base_config.timeout = 300
        base_config.runners = {'python': {'executable': 'python3'}}

        # Create project config file
        project_config_data = {
            'auto_fix': False,
            'runners': {
                'python': {'flags': ['-u']},
                'nodejs': {'executable': 'node'}
            }
        }

        project_config_path = self.project_dir / ".airunner.yaml"
        with open(project_config_path, 'w') as f:
            yaml.dump(project_config_data, f)

        # Merge configurations
        merged_config = base_config.merge_with_project_config(self.project_dir)

        # Check merged values
        assert merged_config.auto_fix is False  # Overridden
        assert merged_config.timeout == 300  # Kept from base

        # Check deep merge of runners
        assert merged_config.runners['python']['executable'] == 'python3'  # From base
        assert merged_config.runners['python']['flags'] == ['-u']  # From project
        assert merged_config.runners['nodejs']['executable'] == 'node'  # From project

    def test_merge_no_project_config(self):
        """Test merging when no project config exists."""
        base_config = Config()

        merged_config = base_config.merge_with_project_config(self.project_dir)

        # Should return the same config
        assert merged_config.auto_fix == base_config.auto_fix
        assert merged_config.timeout == base_config.timeout

    def test_merge_invalid_project_config(self):
        """Test merging with invalid project config."""
        base_config = Config()

        # Create invalid YAML file
        project_config_path = self.project_dir / ".airunner.yaml"
        project_config_path.write_text("invalid: yaml: [")

        with pytest.raises(ValueError, match="Failed to load project config"):
            base_config.merge_with_project_config(self.project_dir)


class TestConfigManager:
    """Test ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigManager.clear_cache()

    def teardown_method(self):
        """Clean up test fixtures."""
        ConfigManager.clear_cache()

    @patch('airun.core.config.Config.load')
    def test_get_config_caching(self, mock_load):
        """Test configuration caching."""
        mock_config = Config()
        mock_load.return_value = mock_config

        # First call should load config
        config1 = ConfigManager.get_config()
        assert mock_load.call_count == 1

        # Second call should use cache
        config2 = ConfigManager.get_config()
        assert mock_load.call_count == 1
        assert config1 is config2

    @patch('airun.core.config.Config.load')
    def test_get_config_force_reload(self, mock_load):
        """Test forced config reload."""
        mock_config = Config()
        mock_load.return_value = mock_config

        # First call
        ConfigManager.get_config()
        assert mock_load.call_count == 1

        # Force reload
        ConfigManager.get_config(force_reload=True)
        assert mock_load.call_count == 2

    def test_clear_cache(self):
        """Test clearing configuration cache."""
        with patch('airun.core.config.Config.load') as mock_load:
            mock_load.return_value = Config()

            # Load config
            ConfigManager.get_config()
            assert ConfigManager._instance is not None

            # Clear cache
            ConfigManager.clear_cache()
            assert ConfigManager._instance is None


class TestConfigHelpers:
    """Test configuration helper functions."""

    def test_validate_llm_provider_valid(self):
        """Test valid LLM provider strings."""
        valid_providers = [
            'ollama:codellama',
            'openai:gpt-4',
            'claude:claude-3-sonnet',
            'anthropic:claude-3-opus'
        ]

        for provider in valid_providers:
            assert validate_llm_provider(provider) is True

    def test_validate_llm_provider_invalid(self):
        """Test invalid LLM provider strings."""
        invalid_providers = [
            '',
            'invalid',
            'provider:',
            ':model',
            'unknown:model',
            None,
            123
        ]

        for provider in invalid_providers:
            assert validate_llm_provider(provider) is False

    def test_get_config_template(self):
        """Test configuration template generation."""
        template = get_config_template()

        assert isinstance(template, str)
        assert 'auto_fix:' in template
        assert 'llm_providers:' in template
        assert 'runners:' in template

        # Should be valid YAML
        parsed = yaml.safe_load(template)
        assert isinstance(parsed, dict)
        assert 'auto_fix' in parsed

    @patch('airun.core.config.Config.load')
    def test_load_config_convenience(self, mock_load):
        """Test load_config convenience function."""
        mock_config = Config()
        mock_load.return_value = mock_config

        result = load_config('/custom/path')

        mock_load.assert_called_once_with('/custom/path')
        assert result is mock_config

    @patch('airun.core.config.ConfigManager.get_config')
    def test_get_config_convenience(self, mock_get):
        """Test get_config convenience function."""
        mock_config = Config()
        mock_get.return_value = mock_config

        result = get_config('/custom/path')

        mock_get.assert_called_once_with('/custom/path')
        assert result is mock_config

    @patch('airun.core.config.Config.create_default_config')
    def test_create_default_config_convenience(self, mock_create):
        """Test create_default_config convenience function."""
        mock_config = Config()
        mock_create.return_value = mock_config

        result = create_default_config(force=True)

        mock_create.assert_called_once_with(True)
        assert result is mock_config


class TestConfigDirectories:
    """Test configuration directory management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_directories(self):
        """Test directory creation."""
        config = Config()
        config.config_dir = Path(self.temp_dir) / "airun"
        config.log_dir = Path(self.temp_dir) / "airun" / "logs"
        config.cache_dir = Path(self.temp_dir) / "airun" / "cache"
        config.backup_dir = Path(self.temp_dir) / "airun" / "backups"

        config.ensure_directories()

        assert config.config_dir.exists()
        assert config.log_dir.exists()
        assert config.cache_dir.exists()
        assert config.backup_dir.exists()

    def test_ensure_directories_permission_error(self):
        """Test directory creation with permission error."""
        config = Config()
        config.config_dir = Path("/root/forbidden")  # Typically no permission

        with pytest.raises(ValueError, match="Failed to create directory"):
            config.ensure_directories()

    def test_create_default_config_file_exists(self):
        """Test creating default config when file exists."""
        config_path = Path(self.temp_dir) / "config.yaml"
        config_path.write_text("existing: config")

        with patch.object(Config, 'get_default_config_path', return_value=config_path):
            with pytest.raises(FileExistsError):
                Config.create_default_config(force=False)

            # Should work with force=True
            result = Config.create_default_config(force=True)
            assert isinstance(result, Config)