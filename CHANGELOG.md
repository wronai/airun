# Changelog

All notable changes to AIRun will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Web interface for AIRun (planned)
- Advanced batch execution features (planned)
- Comprehensive log analysis tools (planned)
- Additional LLM provider support (planned)

## [0.1.0] - 2024-06-04

### Added
- Initial release of AIRun
- Universal script execution for Python, Shell, Node.js, and PHP
- AI-powered error detection and fixing
- Support for multiple LLM providers:
  - Ollama (local LLM support)
  - OpenAI (GPT models)
  - Anthropic Claude
- Intelligent script type detection
- Configurable execution environments
- Comprehensive CLI interface with commands:
  - `airun run` - Execute scripts with AI fixing
  - `airun doctor` - System diagnostics
  - `airun config` - Configuration management
- Real-time error fixing with confidence scoring
- Interactive mode for fix confirmation
- Automatic backup creation before applying fixes
- Comprehensive test suite with 90%+ coverage
- Docker support with multi-stage builds
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Poetry-based dependency management
- Comprehensive documentation

### Features
- **Script Detection**: Automatic detection by extension, shebang, and content analysis
- **Multi-Language Support**: Python, Shell, Node.js, PHP out of the box
- **AI Integration**: Seamless integration with local and cloud LLM providers
- **Error Recovery**: Intelligent error parsing and fix generation
- **Safety Features**: Backup creation, rollback capability, confidence thresholds
- **Configuration**: Flexible YAML-based configuration with environment overrides
- **Logging**: Structured logging with multiple output formats
- **Validation**: Comprehensive input validation and error handling

### Technical
- Python 3.8+ support
- Poetry for dependency management
- Click for CLI framework
- Pydantic for configuration validation
- Comprehensive type hints throughout
- Extensive unit and integration tests
- Docker containerization
- Makefile for development automation

### Documentation
- Complete README with usage examples
- Contributing guidelines
- API documentation
- Docker setup instructions
- Development environment setup
- Configuration reference

## Development Milestones

### Phase 1: Core Functionality ✅
- [x] Script detection and execution
- [x] Basic LLM integration
- [x] Error fixing pipeline
- [x] CLI interface
- [x] Configuration system

### Phase 2: Polish & Testing ✅
- [x] Comprehensive test suite
- [x] Documentation
- [x] CI/CD pipeline
- [x] Docker support
- [x] Code quality tools

### Phase 3: Advanced Features (Planned)
- [ ] Web interface
- [ ] Advanced batch operations
- [ ] Monitoring and metrics
- [ ] Plugin system
- [ ] IDE integrations

### Phase 4: Ecosystem (Planned)
- [ ] Package manager integrations
- [ ] Cloud platform support
- [ ] Team collaboration features
- [ ] Analytics and reporting

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to AIRun.

## License

This project is licensed under the License - see the [LICENSE](LICENSE) file for details.