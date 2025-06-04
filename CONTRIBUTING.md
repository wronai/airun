# Contributing to AIRun 🤝

Thank you for your interest in contributing to AIRun! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Workflow](#contributing-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Poetry for dependency management
- Git for version control
- Basic knowledge of AI/LLM concepts (helpful but not required)

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new functionality
- 🔧 **Code Contributions**: Implement features or fix bugs
- 📚 **Documentation**: Improve or add documentation
- 🧪 **Testing**: Add or improve test coverage
- 🌍 **Translations**: Help make AIRun accessible globally

## 🛠️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/airun.git
cd airun

# Add upstream remote
git remote add upstream https://github.com/original-owner/airun.git
```

### 2. Set Up Development Environment

```bash
# Quick setup using Makefile
make dev-setup

# Or manual setup:
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev,test

# Install pre-commit hooks
poetry run pre-commit install

# Activate virtual environment
poetry shell
```

### 3. Verify Setup

```bash
# Run system check
make doctor

# Run quick tests
make quick-test

# Check code formatting
make format-check
```

## 🔄 Contributing Workflow

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### Branch Naming Conventions

- `feature/feature-name` - New features
- `fix/issue-description` - Bug fixes
- `docs/documentation-update` - Documentation changes
- `test/test-improvements` - Test additions/improvements
- `refactor/code-improvement` - Code refactoring

### 2. Make Changes

```bash
# Make your changes
# ... edit files ...

# Run tests frequently
make test

# Check code quality
make lint
make format
```

### 3. Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Stage your changes
git add .

# Commit with conventional format
git commit -m "feat: add automatic error retry mechanism"
git commit -m "fix: resolve script detection issue with Unicode files"
git commit -m "docs: update installation instructions"
git commit -m "test: add integration tests for Ollama provider"
```

#### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi-colons, etc)
- `refactor`: Code refactoring
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

### 4. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## 📝 Coding Standards

### Python Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security analysis

```bash
# Format code
make format

# Check formatting
make format-check

# Run linting
make lint

# Run all quality checks
make ci
```

### Code Guidelines

1. **Type Hints**: Use type hints for all function parameters and return values
   ```python
   def detect_script_type(filepath: str) -> ScriptType:
       ...
   ```

2. **Documentation**: Use Google-style docstrings
   ```python
   def execute_script(script_path: str, args: List[str]) -> ExecutionResult:
       """
       Execute a script with the appropriate runner.
       
       Args:
           script_path: Path to the script file
           args: Command line arguments to pass to the script
           
       Returns:
           Execution result containing exit code, output, and timing
           
       Raises:
           ExecutionError: If the script cannot be executed
       """
   ```

3. **Error Handling**: Use specific exception types and meaningful error messages
   ```python
   try:
       result = runner.execute(script_path)
   except FileNotFoundError as e:
       raise ExecutionError(f"Script not found: {script_path}") from e
   ```

4. **Logging**: Use structured logging
   ```python
   logger.info("Executing script", extra={
       "script_path": script_path,
       "script_type": script_type.value,
       "args": args
   })
   ```

### Configuration

- Keep configuration in `airun/core/config.py`
- Use environment variables for sensitive data
- Provide sensible defaults
- Validate configuration values

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_detector.py
│   ├── test_runners.py
│   └── test_config.py
├── integration/             # Integration tests
│   ├── test_end_to_end.py
│   └── test_llm_integration.py
├── fixtures/                # Test data
│   ├── scripts/
│   ├── configs/
│   └── outputs/
└── conftest.py             # Pytest configuration
```

### Writing Tests

1. **Test Naming**: Use descriptive names
   ```python
   def test_python_script_detection_by_extension():
       ...
   
   def test_error_fixing_with_syntax_error():
       ...
   ```

2. **Test Categories**: Use pytest markers
   ```python
   @pytest.mark.unit
   def test_config_validation():
       ...
   
   @pytest.mark.integration
   def test_ollama_model_interaction():
       ...
   ```

3. **Fixtures**: Use fixtures for common test data
   ```python
   @pytest.fixture
   def sample_python_script():
       return "print('Hello, World!')"
   ```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-fast          # Unit tests only
make test-integration   # Integration tests only

# Run with coverage
make test-coverage

# Run specific test file
poetry run pytest tests/test_detector.py -v

# Run tests matching pattern
poetry run pytest -k "test_python" -v
```

### Test Requirements

- **Unit Tests**: All new functions and classes must have unit tests
- **Integration Tests**: End-to-end functionality should be covered
- **Coverage**: Maintain >90% code coverage
- **Performance**: Include performance tests for critical paths

## 📚 Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: README, installation guides, usage examples
3. **API Documentation**: Auto-generated from docstrings
4. **Developer Documentation**: Architecture, contributing guidelines

### Writing Documentation

```bash
# Serve documentation locally
make docs-serve

# Build documentation
make docs

# Deploy documentation (maintainers only)
make docs-deploy
```

### Documentation Guidelines

- Use clear, concise language
- Include code examples
- Keep examples up-to-date
- Use proper Markdown formatting
- Add diagrams for complex concepts

## 📤 Submitting Changes

### Pull Request Guidelines

1. **Before Submitting**:
   ```bash
   # Ensure all checks pass
   make ci
   
   # Update your branch with latest main
   git fetch upstream
   git rebase upstream/main
   ```

2. **Pull Request Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes (or clearly documented)
   ```

3. **Pull Request Description**:
   - Clearly describe what the PR does
   - Reference related issues: "Fixes #123"
   - Include screenshots for UI changes
   - Describe any breaking changes

### Review Criteria

Your pull request will be reviewed for:

- **Functionality**: Does it work as intended?
- **Code Quality**: Is it well-written and maintainable?
- **Testing**: Are there adequate tests?
- **Documentation**: Is it properly documented?
- **Performance**: Does it impact performance?
- **Compatibility**: Does it break existing functionality?

## 🔍 Review Process

### For Contributors

1. **Respond to Feedback**: Address review comments promptly
2. **Update Branch**: Keep your branch updated with main
3. **Be Patient**: Reviews may take time, especially for large changes
4. **Ask Questions**: Don't hesitate to ask for clarification

### For Reviewers

1. **Be Constructive**: Provide helpful, actionable feedback
2. **Be Specific**: Point to exact lines and suggest improvements
3. **Be Timely**: Review PRs within reasonable time
4. **Test Changes**: Check out the branch and test manually if needed

## 🎯 Specific Areas for Contribution

### High Priority

- **LLM Provider Support**: Add support for new LLM providers
- **Language Runners**: Add support for new programming languages
- **Error Patterns**: Improve error detection and fixing patterns
- **Performance**: Optimize execution speed and memory usage

### Medium Priority

- **Web Interface**: Develop web-based interface
- **IDE Plugins**: Create plugins for popular IDEs
- **Cloud Integration**: Add cloud provider integrations
- **Monitoring**: Add metrics and monitoring capabilities

### Good for Beginners

- **Documentation**: Improve examples and tutorials
- **Testing**: Add test cases for edge cases
- **Error Messages**: Improve error message clarity
- **Configuration**: Add configuration validation

## 🆘 Getting Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Discord/Slack**: For real-time chat (if available)

### Asking Questions

When asking for help:

1. **Search First**: Check existing issues and documentation
2. **Be Specific**: Provide exact error messages and steps to reproduce
3. **Include Context**: Share your environment details
4. **Show Code**: Include relevant code snippets
5. **Be Patient**: Maintainers are volunteers

### Reporting Bugs

Use this template for bug reports:

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. Use configuration '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.2]
- AIRun version: [e.g., 0.1.0]
- LLM provider: [e.g., Ollama with CodeLlama]

**Additional Context**
Any other context about the problem.
```

## 🏆 Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Credit for specific contributions
- **Documentation**: Author attribution where appropriate

## 📄 License

By contributing to AIRun, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to AIRun! 🚀**

Together, we're building the future of intelligent script execution. Every contribution, no matter how small, makes a difference.