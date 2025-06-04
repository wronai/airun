# AI-Enhanced Universal Interpreter - Plan Wykonania i Architektura

## 1. Założenia Systemu

**Cel:** Jeden interpreter obsługujący Python, Shell, Node.js, PHP z automatycznym naprawianiem błędów w czasie rzeczywistym

**Kluczowe wymagania:**
- Lokalne działanie (bez internetu)
- Routing interpreterów na podstawie rozszerzenia/shebang
- Routing LLM (Ollama, OpenAI, Claude)
- Auto-naprawianie kodu podczas wykonania
- Jedna komenda do uruchomienia dowolnego skryptu

## 2. Architektura Systemu

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Runner CLI                            │
├─────────────────────────────────────────────────────────────┤
│  Input Parser & Script Type Detection                       │
│  ├── File Extension (.py, .sh, .js, .php)                  │
│  ├── Shebang Detection (#!/usr/bin/python, #!/bin/bash)    │
│  └── Content Analysis (fallback detection)                 │
├─────────────────────────────────────────────────────────────┤
│                 Execution Router                            │
│  ├── Python Runner                                         │
│  ├── Shell Runner                                          │
│  ├── Node.js Runner                                        │
│  ├── PHP Runner                                            │
│  └── Custom Runner Extension API                           │
├─────────────────────────────────────────────────────────────┤
│              Error Detection & Handling                     │
│  ├── Real-time Output Monitoring                           │
│  ├── Error Pattern Recognition                             │
│  ├── Context Collection (code + env)                       │
│  └── Auto-retry Logic                                       │
├─────────────────────────────────────────────────────────────┤
│                   LLM Router                               │
│  ├── Provider Selection (Ollama/OpenAI/Claude)            │
│  ├── Model Selection (Code-specialized models)             │
│  ├── Prompt Templates per Language                         │
│  └── Response Processing & Code Extraction                 │
├─────────────────────────────────────────────────────────────┤
│                Configuration Layer                          │
│  ├── ~/.airunner/config.yaml                              │
│  ├── Project-specific .airunner.yaml                      │
│  └── Runtime Settings Override                             │
└─────────────────────────────────────────────────────────────┘
```

## 3. Komponenty Systemu

### 3.1 Core CLI Application
```bash
# Główna komenda
airun script.py          # Auto-detects Python
airun --lang=shell run.sh # Force shell
airun --fix script.js    # Enhanced error fixing
airun --llm=ollama:codellama script.php
```

### 3.2 Script Type Detection Engine
```python
class ScriptDetector:
    def detect_type(self, filepath: str) -> str:
        # 1. Extension mapping
        # 2. Shebang parsing  
        # 3. Content analysis
        # 4. Fallback to user prompt
```

### 3.3 Execution Runners
```python
class BaseRunner:
    def execute(self, script_path: str, args: List[str]) -> ExecutionResult
    def monitor_output(self) -> Generator[str, None, None]
    def handle_error(self, error: Exception) -> FixSuggestion

class PythonRunner(BaseRunner): ...
class ShellRunner(BaseRunner): ...
class NodeRunner(BaseRunner): ...
class PHPRunner(BaseRunner): ...
```

### 3.4 LLM Integration Layer
```python
class LLMRouter:
    providers = {
        'ollama': OllamaProvider,
        'openai': OpenAIProvider, 
        'claude': ClaudeProvider
    }
    
    def fix_error(self, error_context: ErrorContext) -> CodeFix:
        provider = self.get_provider()
        return provider.generate_fix(error_context)
```

## 4. Plan Implementacji

### Faza 1: Core Framework (2-3 tygodnie)
1. **CLI Application Structure**
   - Argument parsing (Click/Typer)
   - Configuration management
   - Basic script detection

2. **Basic Runners Implementation**
   - Python subprocess wrapper
   - Shell command execution
   - Node.js runner
   - PHP runner

3. **Error Detection System**
   - Output stream monitoring
   - Error pattern recognition
   - Exit code handling

### Faza 2: LLM Integration (2-3 tygodnie)
1. **Ollama Integration**
   - Local API client
   - Code Llama model setup
   - Prompt engineering for each language

2. **Multi-Provider Support**
   - OpenAI API integration
   - Claude API integration
   - Provider fallback logic

3. **Error Fixing Engine**
   - Context collection
   - LLM prompt generation
   - Code patch application

### Faza 3: Advanced Features (2-3 tygodnie)
1. **Interactive Mode**
   - Step-by-step debugging
   - User confirmation for fixes
   - Learning from corrections

2. **Performance Optimization**
   - Caching frequent fixes
   - Parallel execution
   - Memory management

3. **Extensions & Plugins**
   - Custom runner plugins
   - Language-specific enhancements
   - IDE integrations

## 5. Przykładowa Konfiguracja

```yaml
# ~/.airunner/config.yaml
default_llm: "ollama:codellama"
auto_fix: true
interactive_mode: false

llm_providers:
  ollama:
    base_url: "http://localhost:11434"
    models:
      python: "codellama:13b"
      javascript: "codellama:13b"
      shell: "mistral:7b"
      php: "codellama:13b"
      
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
    
runners:
  python:
    executable: "python3"
    flags: ["-u"]  # unbuffered output
    
  nodejs:
    executable: "node"
    flags: ["--experimental-modules"]
    
languages:
  python:
    extensions: [".py", ".pyw"]
    shebangs: ["#!/usr/bin/python", "#!/usr/bin/env python"]
    
  shell:
    extensions: [".sh", ".bash", ".zsh"]
    shebangs: ["#!/bin/bash", "#!/bin/zsh"]
```

## 6. Przykład Użycia

```bash
# Instalacja
pip install airunner
# lub
cargo install airunner

# Podstawowe użycie
airun script.py
airun deploy.sh --args="production"
airun server.js --port=3000

# Z wymuszonym językiem
airun --lang=python script.txt
airun --lang=shell commands.txt

# Z konkretnym LLM
airun --llm=ollama:codellama script.py
airun --llm=openai:gpt-4 debug_this.js

# Tryb interaktywny
airun --interactive problematic_script.py

# Tylko analiza bez wykonania
airun --analyze-only script.sh
```

## 7. Rozszerzenia Przyszłości

1. **IDE Plugins**
   - VS Code extension
   - Vim/Neovim plugin
   - IntelliJ plugin

2. **CI/CD Integration**
   - GitHub Actions
   - GitLab CI
   - Jenkins plugin

3. **Collaborative Features**
   - Team fix sharing
   - Knowledge base building
   - Custom model training

4. **Advanced Analytics**
   - Error pattern analysis
   - Performance metrics
   - Learning recommendations

## 8. Technologie i Zależności

**Core:**
- Python 3.8+ (główny język implementacji)
- Click/Typer (CLI framework)
- asyncio (asynchronous execution)
- pydantic (configuration management)

**LLM Integration:**
- ollama-python (Ollama client)
- openai (OpenAI API)
- anthropic (Claude API)

**Process Management:**
- subprocess32 (enhanced subprocess)
- psutil (process monitoring)

**Configuration:**
- PyYAML (config files)
- python-dotenv (environment variables)

To rozwiązanie będzie działać jako uniwersalny wrapper dla wszystkich interpreterów z inteligentnym wsparciem AI działającym lokalnie.