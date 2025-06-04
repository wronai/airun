# AIRun Project Makefile
# Comprehensive development and deployment automation

.PHONY: help install dev-setup test lint format build clean docs docker release

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Project variables
PROJECT_NAME = airun
PYTHON = python3
PIP = pip3
POETRY = poetry
DOCKER_IMAGE = airun
VERSION = $(shell poetry version -s)

# Help target
help: ## Show this help message
	@echo "$(BLUE)AIRun Development Makefile$(NC)"
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install AIRun for production use
	@echo "$(BLUE)Installing AIRun...$(NC)"
	$(PIP) install .
	@echo "$(GREEN)✅ Installation complete$(NC)"

install-dev: ## Install AIRun in development mode
	@echo "$(BLUE)Installing AIRun in development mode...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)✅ Development installation complete$(NC)"

install-poetry: ## Install using Poetry
	@echo "$(BLUE)Installing with Poetry...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)✅ Poetry installation complete$(NC)"

# Development setup
dev-setup: ## Setup complete development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@command -v poetry >/dev/null 2>&1 || { echo "$(RED)❌ Poetry not found. Installing...$(NC)"; curl -sSL https://install.python-poetry.org | python3 -; }
	$(POETRY) install --with dev,test
	$(POETRY) run pre-commit install
	mkdir -p tests/fixtures/{scripts,configs,outputs}
	$(MAKE) create-test-scripts
	$(MAKE) setup-ollama
	@echo "$(GREEN)✅ Development environment ready$(NC)"

create-test-scripts: ## Create test script fixtures
	@echo "$(BLUE)Creating test scripts...$(NC)"
	@mkdir -p tests/fixtures/scripts
	@echo 'print("Hello World")' > tests/fixtures/scripts/test_python.py
	@echo 'print("Missing parenthesis"' > tests/fixtures/scripts/broken_python.py
	@echo '#!/bin/bash\necho "Hello World"' > tests/fixtures/scripts/test_shell.sh
	@echo '#!/bin/bash\necho Hello $$UNDEFINED_VAR' > tests/fixtures/scripts/broken_shell.sh
	@echo 'console.log("Hello World");' > tests/fixtures/scripts/test_node.js
	@echo 'console.log("Missing semicolon")' > tests/fixtures/scripts/broken_node.js
	@echo '<?php echo "Hello World"; ?>' > tests/fixtures/scripts/test_php.php
	@echo '<?php echo "Missing semicolon"' > tests/fixtures/scripts/broken_php.php
	@chmod +x tests/fixtures/scripts/*.sh
	@echo "$(GREEN)✅ Test scripts created$(NC)"

setup-ollama: ## Setup Ollama for local AI testing
	@echo "$(BLUE)Setting up Ollama...$(NC)"
	@if command -v ollama >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Ollama already installed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh$(NC)"; \
	fi
	@if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Ollama service running$(NC)"; \
		ollama pull codellama:7b || echo "$(YELLOW)⚠️  Failed to pull codellama:7b$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Ollama service not running. Start with: ollama serve$(NC)"; \
	fi

# Testing targets
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(POETRY) run pytest -v --tb=short

test-fast: ## Run tests without integration tests
	@echo "$(BLUE)Running fast tests...$(NC)"
	$(POETRY) run pytest -v --tb=short -m "not integration"

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(POETRY) run pytest -v --tb=short -m integration

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(POETRY) run pytest --cov=airun --cov-report=html --cov-report=term --cov-report=xml
	@echo "$(GREEN)📊 Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(POETRY) run ptw --runner "pytest -v --tb=short"

# Code quality targets
lint: ## Run all linting tools
	@echo "$(BLUE)Running linters...$(NC)"
	$(POETRY) run flake8 airun tests
	$(POETRY) run mypy airun
	$(POETRY) run bandit -r airun
	@echo "$(GREEN)✅ Linting complete$(NC)"

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	$(POETRY) run black airun tests
	$(POETRY) run isort airun tests
	@echo "$(GREEN)✅ Auto-fixes applied$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(POETRY) run black airun tests
	$(POETRY) run isort airun tests
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(POETRY) run black --check airun tests
	$(POETRY) run isort --check-only airun tests

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	$(POETRY) run bandit -r airun
	$(POETRY) run safety check
	@echo "$(GREEN)✅ Security check complete$(NC)"

# Build targets
build: ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	$(POETRY) build
	@echo "$(GREEN)✅ Package built: dist/$(NC)"

build-wheel: ## Build wheel only
	@echo "$(BLUE)Building wheel...$(NC)"
	$(POETRY) build --format wheel

build-sdist: ## Build source distribution only
	@echo "$(BLUE)Building source distribution...$(NC)"
	$(POETRY) build --format sdist

# Documentation targets
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	$(POETRY) run mkdocs build
	@echo "$(GREEN)📚 Documentation built: site/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000$(NC)"
	$(POETRY) run mkdocs serve

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)Deploying documentation...$(NC)"
	$(POETRY) run mkdocs gh-deploy

# Docker targets
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(VERSION) -t $(DOCKER_IMAGE):latest .
	@echo "$(GREEN)✅ Docker image built$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run --rm -it -v $(PWD):/workspace $(DOCKER_IMAGE):latest

docker-test: ## Run tests in Docker
	@echo "$(BLUE)Running tests in Docker...$(NC)"
	docker run --rm -v $(PWD):/workspace $(DOCKER_IMAGE):latest make test

docker-push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	docker push $(DOCKER_IMAGE):$(VERSION)
	docker push $(DOCKER_IMAGE):latest

# Examples and demonstrations
demo: ## Run demonstration scripts
	@echo "$(BLUE)Running AIRun demonstration...$(NC)"
	@$(MAKE) create-demo-scripts
	@echo "$(YELLOW)Demo 1: Python script with syntax error$(NC)"
	$(POETRY) run airun examples/demo/broken_python.py || true
	@echo "\n$(YELLOW)Demo 2: Shell script with permission issues$(NC)"
	$(POETRY) run airun examples/demo/broken_shell.sh || true
	@echo "\n$(YELLOW)Demo 3: Successful execution$(NC)"
	$(POETRY) run airun examples/demo/working_script.py

create-demo-scripts: ## Create demonstration scripts
	@mkdir -p examples/demo
	@echo 'print("This works!")' > examples/demo/working_script.py
	@echo 'print("Missing closing parenthesis"' > examples/demo/broken_python.py
	@echo '#!/bin/bash\nmkdir /restricted/folder' > examples/demo/broken_shell.sh
	@chmod +x examples/demo/broken_shell.sh

examples: ## Generate example configurations and scripts
	@echo "$(BLUE)Generating examples...$(NC)"
	$(POETRY) run airun examples --output examples/
	@echo "$(GREEN)✅ Examples created in examples/$(NC)"

# Benchmarking and performance
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	$(POETRY) run python scripts/benchmark.py
	@echo "$(GREEN)📊 Benchmark results saved$(NC)"

profile: ## Profile application performance
	@echo "$(BLUE)Profiling application...$(NC)"
	$(POETRY) run python -m cProfile -o profile.stats scripts/profile_runner.py
	$(POETRY) run python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Release targets
pre-release: ## Prepare for release (run all quality checks)
	@echo "$(BLUE)Preparing for release...$(NC)"
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test-coverage
	$(MAKE) docs
	$(MAKE) build
	@echo "$(GREEN)✅ Pre-release checks passed$(NC)"

release-patch: ## Release patch version (0.0.x)
	@echo "$(BLUE)Releasing patch version...$(NC)"
	$(POETRY) version patch
	$(MAKE) pre-release
	@echo "$(GREEN)✅ Ready for patch release: $(shell poetry version -s)$(NC)"

release-minor: ## Release minor version (0.x.0)
	@echo "$(BLUE)Releasing minor version...$(NC)"
	$(POETRY) version minor
	$(MAKE) pre-release
	@echo "$(GREEN)✅ Ready for minor release: $(shell poetry version -s)$(NC)"

release-major: ## Release major version (x.0.0)
	@echo "$(BLUE)Releasing major version...$(NC)"
	$(POETRY) version major
	$(MAKE) pre-release
	@echo "$(GREEN)✅ Ready for major release: $(shell poetry version -s)$(NC)"

publish: ## Publish package to PyPI
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	$(POETRY) publish
	@echo "$(GREEN)✅ Package published$(NC)"

publish-test: ## Publish package to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	$(POETRY) publish --repository testpypi
	@echo "$(GREEN)✅ Package published to TestPyPI$(NC)"

# Git and version control
tag: ## Create git tag for current version
	@echo "$(BLUE)Creating git tag...$(NC)"
	git tag v$(VERSION)
	git push origin v$(VERSION)
	@echo "$(GREEN)✅ Tag v$(VERSION) created and pushed$(NC)"

# Maintenance targets
clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(BLUE)Deep cleaning...$(NC)"
	$(POETRY) env remove --all || true
	rm -rf .venv/
	@echo "$(GREEN)✅ Deep cleanup complete$(NC)"

reset: clean-all dev-setup ## Reset development environment
	@echo "$(BLUE)Resetting development environment...$(NC)"
	@echo "$(GREEN)✅ Environment reset$(NC)"

# Utility targets
check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(NC)"
	$(POETRY) show --outdated

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(POETRY) update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

install-hooks: ## Install git hooks
	@echo "$(BLUE)Installing git hooks...$(NC)"
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✅ Git hooks installed$(NC)"

run-hooks: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	$(POETRY) run pre-commit run --all-files

doctor: ## Run AIRun system diagnostics
	@echo "$(BLUE)Running system diagnostics...$(NC)"
	$(POETRY) run airun doctor

# CI/CD simulation
ci: ## Simulate CI pipeline locally
	@echo "$(BLUE)Simulating CI pipeline...$(NC)"
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test-coverage
	$(MAKE) build
	@echo "$(GREEN)✅ CI simulation passed$(NC)"

# Development utilities
shell: ## Open Poetry shell
	@echo "$(BLUE)Opening Poetry shell...$(NC)"
	$(POETRY) shell

install-local: ## Install current version locally
	@echo "$(BLUE)Installing local version...$(NC)"
	$(PIP) uninstall -y $(PROJECT_NAME) || true
	$(PIP) install -e .
	@echo "$(GREEN)✅ Local version installed$(NC)"

# Information targets
info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "Name: $(PROJECT_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Python: $(shell python --version)"
	@echo "Poetry: $(shell poetry --version)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo "Git commit: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"

version: ## Show current version
	@echo "$(GREEN)$(PROJECT_NAME) v$(VERSION)$(NC)"

# Dependencies check
check-