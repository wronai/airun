# AIRun 🚀

**AI-Enhanced Universal Script Runner with Automatic Error Fixing**

AIRun is a powerful command-line tool that can execute scripts in multiple languages (Python, Shell, Node.js, PHP) with intelligent AI-powered error detection and automatic fixing capabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

- 🔄 **Universal Script Execution** - One command for Python, Shell, Node.js, and PHP scripts
- 🤖 **AI-Powered Error Fixing** - Automatic detection and fixing of common errors
- 🎯 **Smart Language Detection** - Automatically detects script type from extension, shebang, or content
- 🔌 **Multiple LLM Support** - Works with Ollama (local), OpenAI, Claude/Anthropic
- ⚡ **Real-time Error Handling** - Fixes errors during execution with configurable retry attempts
- 🛡️ **Safe Execution** - Creates backups before applying fixes
- 📊 **Detailed Analysis** - Comprehensive script analysis and diagnostics
- 🎛️ **Highly Configurable** - Project-specific and global configuration support

## 🚀 Quick Start

### Installation

#### Option 1: Using pip (when published)
```bash
pip install airun
```

#### Option 2: From source
```bash
# Clone the repository
git clone https://github.com/wronai/airun.git
cd airun

# Install with Poetry
poetry install
poetry shell

# Or install with pip
pip install -e .
```

#### Option 3: One-line installer
```bash
curl -sSL https://raw.githubusercontent.com/wronai/airun/main/scripts/install.sh | bash
```

### Setup Ollama (for local AI)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Download Code Llama model
ollama pull codellama:7b
```

### Initialize Configuration
```bash
# Create default configuration
airun config --init

# Check system status
airun doctor
```

## 📖 Usage Examples

### Basic Script Execution

```bash
# Auto-detect and run Python script
airun my_script.py

# Auto-detect and run shell script
airun deploy.sh production

# Force specific language
airun --lang=nodejs app.js

# Run with arguments
airun data_processor.py --input data.csv --output results.json
```

### AI-Enhanced Error Fixing

```bash
# Run with automatic error fixing (default)
airun broken_script.py

# Disable automatic fixing
airun --no-fix risky_script.sh

# Interactive mode (confirm before applying fixes)
airun --interactive debug_me.py

# Specify LLM provider
airun --llm=openai:gpt-4 complex_script.py
airun --llm=ollama:codellama:13b performance_critical.py
```

### Analysis and Debugging

```bash
# Analyze script without execution
airun analyze my_script.py

# Dry run (validate and show execution plan)
airun run --dry-run script.py

# Verbose output for debugging
airun run --verbose script.py

# Generate analysis report
airun analyze --output=report.json --format=json script.py
```

### Batch Operations

```bash
# Run multiple scripts
airun batch script1.py script2.sh script3.js

# Parallel execution
airun batch --parallel *.py

# Stop on first error
airun batch --stop-on-error test_*.py

# Generate execution report
airun batch --report=results.html *.py
```

### Configuration Management

```bash
# Show current configuration
airun config --show

# Edit configuration
airun config --edit

# Set configuration values
airun config --set auto_fix=false
airun config --set llm_providers.ollama.base_url=http://localhost:11434
```

## 📋 Real-World Examples

### Example 1: Python Script with Syntax Error

**broken_script.py:**
```python
import sys
import os

def process_data(filename):
    with open(filename, 'r') as f:
        data = f.read()
    
    # Missing closing parenthesis - syntax error
    result = data.replace('old', 'new'
    return result

if __name__ == "__main__":
    process_data(sys.argv[1])
```

**Run with AIRun:**
```bash
$ airun broken_script.py data.txt

🚀 Executing broken_script.py (python)
❌ Error detected: SyntaxError: unexpected EOF while parsing
🤖 Attempting AI fix...
🔧 Applied AI fix, retrying...
✅ Error fixed successfully!
Data processed successfully
✅ Execution completed in 1.23s
```

### Example 2: Shell Script with Permission Issues

**setup.sh:**
```bash
#!/bin/bash
mkdir /opt/myapp
cp files/* /opt/myapp/
chmod +x /opt/myapp/start.sh
```

**Run with AIRun:**
```bash
$ airun setup.sh

🚀 Executing setup.sh (shell)
❌ Error detected: Permission denied
🤖 Attempting AI fix...
🔧 Applied AI fix, retrying...
# AI adds 'sudo' where needed
✅ Error fixed successfully!
✅ Execution completed in 2.45s
```

### Example 3: Node.js with Missing Dependencies

**app.js:**
```javascript
const express = require('express');
const missingModule = require('missing-package');

const app = express();
app.listen(3000);
```

**Run with AIRun:**
```bash
$ airun app.js

🚀 Executing app.js (nodejs)
❌ Error detected: Cannot find module 'missing-package'
🤖 Attempting AI fix...
🔧 Applied AI fix, retrying...
# AI suggests removing unused import or installing package
✅ Error fixed successfully!
Server running on port 3000
✅ Execution completed in 3.12s
```

## ⚙️ Configuration

### Global Configuration

AIRun uses `~/.airun/config.yaml` for global settings:

```yaml
# Core Settings
auto_fix: true
interactive_mode: false
timeout: 300
max_retries: 3

# Default LLM Provider
default_llm: "ollama:codellama"

# LLM Providers
llm_providers:
  ollama:
    base_url: "http://localhost:11434"
    models:
      python: "codellama:7b"
      shell: "codellama:7b"
      nodejs: "codellama:7b"
      php: "codellama:7b"
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
  
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"

# Script Runners
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
```

### Project-Specific Configuration

Create `.airunner.yaml` in your project directory:

```yaml
# Override global settings for this project
default_llm: "openai:gpt-4"
auto_fix: true

runners:
  python:
    executable: "python3.11"
    flags: ["-u", "-X", "dev"]
  
  nodejs:
    executable: "node"
    flags: ["--experimental-modules"]

# Custom prompts for this project
prompts:
  python:
    system: "You are debugging a Django web application. Consider Django patterns and best practices."
```

### Environment Variables

Override configuration with environment variables:

```bash
export AIRUN_AUTO_FIX=false
export AIRUN_DEFAULT_LLM="openai:gpt-4"
export AIRUN_TIMEOUT=600
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-claude-key"
```

## 🔧 Advanced Usage

### Custom Model Configuration

```bash
# Use specific Ollama model
airun --llm=ollama:codellama:13b large_script.py

# Use OpenAI with specific model
airun --llm=openai:gpt-4-turbo complex_analysis.py

# Use Claude for shell scripts
airun --llm=claude:claude-3-opus advanced_deploy.sh
```

### Integration with CI/CD

**.github/workflows/ai-test.yml:**
```yaml
name: AI-Enhanced Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup AIRun
      run: |
        curl -sSL https://raw.githubusercontent.com/wronai/airun/main/scripts/install.sh | bash
        airun doctor
    - name: Run tests with AI fixing
      run: |
        airun batch --report=test_results.html test_*.py
        airun batch --parallel --max-retries=1 integration_tests/*.sh
```

### IDE Integration

**VS Code Task (.vscode/tasks.json):**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AIRun: Execute Current File",
      "type": "shell",
      "command": "airun",
      "args": ["${file}"],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/wronai/airun.git
cd airun

# Setup development environment
make dev-setup

# Run tests
make test

# Run linting
make lint

# Build package
make build
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_detector.py -v

# Run integration tests (requires real interpreters)
pytest tests/ -m integration
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `make test`
5. Submit a pull request

## 📊 Comparison with Other Tools

| Feature | AIRun | Traditional Runners | Other AI Tools |
|---------|-------|-------------------|----------------|
| Multi-language support | ✅ | ❌ | ⚠️ |
| Auto error fixing | ✅ | ❌ | ⚠️ |
| Local AI support | ✅ | ❌ | ❌ |
| Script analysis | ✅ | ❌ | ⚠️ |
| Backup/restore | ✅ | ❌ | ❌ |
| Batch execution | ✅ | ⚠️ | ❌ |
| Configuration flexibility | ✅ | ⚠️ | ⚠️ |

## 🚨 Safety Features

- **Automatic Backups**: Creates backups before applying any fixes
- **Confirmation Prompts**: Interactive mode asks before applying changes
- **Rollback Capability**: Can restore original files if fixes fail
- **Dry Run Mode**: Analyze and validate without execution
- **Configurable Limits**: Set maximum retry attempts and timeouts

## 🤖 Supported LLM Providers

### Ollama (Local)
- **Models**: CodeLlama, Mistral, Llama 2, custom models
- **Benefits**: Free, private, offline capable
- **Setup**: `ollama pull codellama:7b`

### OpenAI
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Benefits**: High quality, fast response
- **Setup**: Set `OPENAI_API_KEY` environment variable

### Anthropic (Claude)
- **Models**: Claude 3 Sonnet, Claude 3 Opus
- **Benefits**: Excellent reasoning, safety-focused
- **Setup**: Set `ANTHROPIC_API_KEY` environment variable

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api/)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 🆘 Troubleshooting

### Common Issues

**1. "Unable to determine script type"**
```bash
# Use --lang to force detection
airun --lang=python ambiguous_file.txt
```

**2. "Required executable not found"**
```bash
# Check system status
airun doctor

# Install missing interpreters
# Ubuntu/Debian: apt install python3 nodejs php-cli
# macOS: brew install python node php
```

**3. "Ollama connection failed"**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull required model
ollama pull codellama:7b
```

**4. "AI fix failed"**
```bash
# Try different model
airun --llm=openai:gpt-4 script.py

# Use interactive mode
airun --interactive script.py

# Disable AI fixing for debugging
airun --no-fix script.py
```

### Getting Help

```bash
# System diagnosis
airun doctor

# View logs
airun logs --days=7

# Verbose execution
airun run --verbose script.py

# Get configuration template
airun config --init
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [OpenAI](https://openai.com/) for GPT models
- [Anthropic](https://anthropic.com/) for Claude models
- [Click](https://click.palletsprojects.com/) for CLI framework
- All contributors and users of this project

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wronai/airun&type=Date)](https://star-history.com/#wronai/airun&Date)

---

**Made with ❤️ by the AIRun team**

*If you find AIRun useful, please consider giving it a star ⭐ and sharing it with others!*



# AIRun Project Tree Structure

## 📁 Current Project Structure (as `tree` command output)

```
airun/
├── README.md                              ✅ COMPLETE
├── LICENSE                                ❌ MISSING
├── CONTRIBUTING.md                        ✅ COMPLETE
├── CHANGELOG.md                           ❌ MISSING
├── CODE_OF_CONDUCT.md                     ❌ MISSING
├── pyproject.toml                         ✅ COMPLETE
├── poetry.lock                            ❌ GENERATED (after poetry install)
├── Makefile                               ✅ COMPLETE
├── Dockerfile                             ✅ COMPLETE
├── docker-compose.yml                     ✅ COMPLETE
├── .gitignore                             ❌ MISSING
├── .pre-commit-config.yaml                ❌ MISSING
├── .dockerignore                          ❌ MISSING
├── .github/
│   └── workflows/
│       ├── ci.yml                         ✅ COMPLETE
│       ├── release.yml                    ❌ MISSING
│       └── ISSUE_TEMPLATE/
│           ├── bug_report.md              ❌ MISSING
│           ├── feature_request.md         ❌ MISSING
│           └── config.yml                 ❌ MISSING
├── airun/
│   ├── __init__.py                        ✅ COMPLETE
│   ├── __main__.py                        ❌ MISSING
│   ├── cli.py                             ✅ COMPLETE (needs imports fix)
│   ├── core/
│   │   ├── __init__.py                    ❌ MISSING
│   │   ├── detector.py                    ✅ COMPLETE
│   │   ├── runners.py                     ✅ COMPLETE
│   │   ├── config.py                      ✅ COMPLETE
│   │   ├── llm_router.py                  ❌ MISSING
│   │   └── ai_fixer.py                    ❌ MISSING
│   ├── providers/
│   │   ├── __init__.py                    ❌ MISSING
│   │   ├── base.py                        ❌ MISSING
│   │   ├── ollama.py                      ❌ MISSING
│   │   ├── openai.py                      ❌ MISSING
│   │   └── claude.py                      ❌ MISSING
│   ├── utils/
│   │   ├── __init__.py                    ❌ MISSING
│   │   ├── file_ops.py                    ❌ MISSING
│   │   ├── logging.py                     ❌ MISSING
│   │   ├── validation.py                  ❌ MISSING
│   │   ├── analyzer.py                    ❌ MISSING
│   │   ├── batch_executor.py              ❌ MISSING
│   │   ├── log_viewer.py                  ❌ MISSING
│   │   ├── cleaner.py                     ❌ MISSING
│   │   └── examples.py                    ❌ MISSING
│   ├── templates/
│   │   ├── prompts/
│   │   │   ├── python.txt                 ❌ MISSING
│   │   │   ├── shell.txt                  ❌ MISSING
│   │   │   ├── nodejs.txt                 ❌ MISSING
│   │   │   └── php.txt                    ❌ MISSING
│   │   └── config/
│   │       └── default.yaml               ❌ MISSING
│   └── web/                               ❌ OPTIONAL (future enhancement)
│       ├── __init__.py
│       ├── app.py
│       └── templates/
├── tests/
│   ├── __init__.py                        ❌ MISSING
│   ├── conftest.py                        ❌ MISSING
│   ├── test_detector.py                   ✅ COMPLETE
│   ├── test_runners.py                    ✅ COMPLETE
│   ├── test_config.py                     ✅ COMPLETE
│   ├── test_cli.py                        ✅ COMPLETE (needs imports fix)
│   ├── test_llm_router.py                 ❌ MISSING
│   ├── fixtures/
│   │   ├── scripts/
│   │   │   ├── test.py                    ❌ GENERATED (by Makefile)
│   │   │   ├── test.sh                    ❌ GENERATED (by Makefile)
│   │   │   ├── test.js                    ❌ GENERATED (by Makefile)
│   │   │   ├── test.php                   ❌ GENERATED (by Makefile)
│   │   │   ├── broken_python.py           ❌ GENERATED (by Makefile)
│   │   │   ├── broken_shell.sh            ❌ GENERATED (by Makefile)
│   │   │   ├── broken_node.js             ❌ GENERATED (by Makefile)
│   │   │   └── broken_php.php             ❌ GENERATED (by Makefile)
│   │   └── configs/
│   │       └── test_config.yaml           ❌ MISSING
│   └── integration/
│       ├── __init__.py                    ❌ MISSING
│       ├── test_end_to_end.py             ❌ MISSING
│       └── test_ollama_integration.py     ❌ MISSING
├── docs/
│   ├── index.md                           ❌ MISSING
│   ├── installation.md                    ❌ MISSING
│   ├── configuration.md                   ❌ MISSING
│   ├── usage.md                           ❌ MISSING
│   ├── api/
│   │   ├── core.md                        ❌ MISSING
│   │   └── providers.md                   ❌ MISSING
│   ├── examples/
│   │   ├── basic_usage.md                 ❌ MISSING
│   │   └── advanced_config.md             ❌ MISSING
│   └── mkdocs.yml                         ❌ MISSING
├── scripts/
│   ├── install.sh                         ❌ MISSING
│   ├── setup_ollama.sh                    ❌ MISSING
│   ├── setup_dev.sh                       ❌ MISSING
│   ├── release.sh                         ❌ MISSING
│   ├── benchmark.py                       ❌ MISSING
│   ├── profile_runner.py                  ❌ MISSING
│   ├── stress_test.py                     ❌ MISSING
│   ├── memory_test.py                     ❌ MISSING
│   └── seed_data.py                       ❌ MISSING
├── examples/
│   ├── config_examples/
│   │   ├── minimal.yaml                   ❌ MISSING
│   │   ├── full_featured.yaml             ❌ MISSING
│   │   └── team_config.yaml               ❌ MISSING
│   ├── broken_scripts/
│   │   ├── syntax_error.py                ❌ MISSING
│   │   ├── missing_deps.js                ❌ MISSING
│   │   └── permission_error.sh            ❌ MISSING
│   └── demo/
│       ├── run_demo.py                    ❌ MISSING
│       └── showcase.sh                    ❌ MISSING
├── monitoring/                            ❌ OPTIONAL
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
├── nginx/                                 ❌ OPTIONAL
│   ├── nginx.conf
│   └── ssl/
└── babel.cfg                              ❌ OPTIONAL (i18n)
```

## 🔧 Files That Need to be Created/Fixed

### 🚨 CRITICAL (Required for basic functionality)

#### Missing Core Modules:
1. **`airun/core/__init__.py`**
2. **`airun/core/llm_router.py`** - LLM provider routing logic
3. **`airun/core/ai_fixer.py`** - AI error fixing implementation
4. **`airun/providers/`** - Complete LLM provider implementations
5. **`airun/utils/`** - All utility modules
6. **`airun/__main__.py`** - Entry point for `python -m airun`

#### Missing Configuration Files:
7. **`.gitignore`** - Git ignore patterns
8. **`.pre-commit-config.yaml`** - Pre-commit hooks
9. **`LICENSE`** - MIT License file
10. **`airun/templates/config/default.yaml`** - Default configuration

#### Missing Test Infrastructure:
11. **`tests/__init__.py`** and **`tests/conftest.py`**
12. **`tests/test_llm_router.py`** - LLM router tests
13. **`tests/fixtures/configs/test_config.yaml`** - Test configuration

### ⚠️ IMPORTANT (Required for full functionality)

#### CLI Import Fixes:
14. **Fix imports in `airun/cli.py`** - Missing imports for new modules
15. **Fix imports in `tests/test_cli.py`** - Test import issues

#### Installation Scripts:
16. **`scripts/install.sh`** - Production installation script
17. **`scripts/setup_ollama.sh`** - Ollama setup automation
18. **`scripts/setup_dev.sh`** - Development environment setup

#### Documentation:
19. **`docs/mkdocs.yml`** - MkDocs configuration
20. **`CHANGELOG.md`** - Version history
21. **`CODE_OF_CONDUCT.md`** - Community guidelines

### 📝 NICE TO HAVE (Enhancement features)

#### GitHub Templates:
22. **`.github/ISSUE_TEMPLATE/`** - Issue templates
23. **`.github/workflows/release.yml`** - Release automation

#### Examples and Demos:
24. **`examples/`** - Example configurations and scripts
25. **`scripts/benchmark.py`** - Performance benchmarking

#### Advanced Features:
26. **`airun/web/`** - Web interface (future)
27. **`monitoring/`** - Monitoring configurations (optional)

## 🛠️ Files That Need Fixes

### `airun/cli.py` Import Issues:
```python
# Missing imports that need to be added:
from .core.llm_router import LLMRouter
from .core.ai_fixer import AIFixer
from .utils.logging import setup_logging, get_logger
from .utils.validation import validate_script_path, validate_llm_provider
from .utils.analyzer import ScriptAnalyzer
from .utils.batch_executor import BatchExecutor
from .utils.log_viewer import LogViewer
from .utils.cleaner import DataCleaner
from .utils.examples import ExampleGenerator
```

### `tests/test_cli.py` Import Issues:

```python
# Missing imports that need to be added:
from airun2.utils.analyzer import ScriptAnalyzer
from airun2.utils.batch_executor import BatchExecutor
```

## ⚡ Priority Order for Creation

### Phase 1: Core Functionality (MUST HAVE)
1. Create all `__init__.py` files
2. Implement `airun/core/llm_router.py`
3. Implement `airun/core/ai_fixer.py`
4. Implement `airun/providers/` modules
5. Create `.gitignore` and basic config files
6. Fix CLI imports

### Phase 2: Essential Utils (SHOULD HAVE)
7. Implement `airun/utils/` modules
8. Create test infrastructure files
9. Create installation scripts
10. Create basic documentation

### Phase 3: Polish & Enhancement (NICE TO HAVE)
11. Create examples and demos
12. Add GitHub templates
13. Create monitoring and advanced features

## 🚀 Quick Start Commands

```bash
# After creating missing files, run:
make dev-setup          # Will generate test fixtures
poetry install          # Will create poetry.lock
make create-test-scripts # Will create test script fixtures
make doctor             # Will validate setup
```

This structure provides a clear roadmap for completing the AIRun project with all necessary components.