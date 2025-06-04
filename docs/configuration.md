# AI Runner - Setup Instructions

## Instalacja

### 1. Wymagania systemowe
```bash
# Python 3.8+
python3 --version

# Ollama (dla lokalnego LLM)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pobierz model Code Llama
ollama pull codellama:7b
```

### 2. Instalacja AI Runner
```bash
# Klonuj repo lub zapisz kod
mkdir airunner && cd airunner

# Zainstaluj zależności
pip install click pyyaml requests

# Utwórz plik airunner.py z kodem
# Nadaj uprawnienia wykonawcze
chmod +x airunner.py

# Opcjonalnie: dodaj do PATH
sudo ln -s $(pwd)/airunner.py /usr/local/bin/airun
```

### 3. Konfiguracja

Utwórz plik `~/.airunner/config.yaml`:

```yaml
# Domyślne ustawienia
default_llm: "ollama:codellama"
auto_fix: true
interactive_mode: false
timeout: 300  # 5 minut

# Konfiguracja LLM providers
llm_providers:
  ollama:
    base_url: "http://localhost:11434"
    models:
      python: "codellama:7b"
      javascript: "codellama:7b" 
      shell: "codellama:7b"
      php: "codellama:7b"
      
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
    
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet-20240229"

# Konfiguracja interpreterów
runners:
  python:
    executable: "python3"
    flags: ["-u", "-W", "ignore"]  # unbuffered, ignore warnings
    
  shell:
    executable: "bash"
    flags: ["-e"]  # exit on error
    
  nodejs:
    executable: "node"
    flags: ["--experimental-modules"]
    
  php:
    executable: "php"
    flags: ["-f"]

# Wykrywanie typów plików
languages:
  python:
    extensions: [".py", ".pyw", ".py3"]
    shebangs: ["#!/usr/bin/python", "#!/usr/bin/env python", "#!/usr/bin/python3"]
    content_patterns: ["import ", "def ", "print(", "if __name__"]
    
  shell:
    extensions: [".sh", ".bash", ".zsh", ".fish"]
    shebangs: ["#!/bin/bash", "#!/bin/sh", "#!/usr/bin/env bash", "#!/bin/zsh"]
    content_patterns: ["echo ", "export ", "chmod ", "mkdir ", "cd "]
    
  nodejs:
    extensions: [".js", ".mjs", ".ts", ".jsx", ".tsx"]
    shebangs: ["#!/usr/bin/node", "#!/usr/bin/env node"]
    content_patterns: ["console.log", "require(", "import ", "function ", "const ", "let "]
    
  php:
    extensions: [".php", ".php3", ".php4", ".php5", ".phtml"]
    shebangs: ["#!/usr/bin/php", "#!/usr/bin/env php"]
    content_patterns: ["<?php", "echo ", "$_GET", "$_POST", "function "]

# Ustawienia naprawiania błędów
error_fixing:
  max_retries: 3
  confidence_threshold: 0.6
  backup_files: true
  interactive_confirm: false
  
# Prompty dla różnych języków
prompts:
  python:
    system: "You are a Python debugging expert. Fix code errors with minimal changes."
    error_template: |
      Fix this Python error:
      
      Error: {error_message}
      File: {file_path}
      Line: {line_number}
      
      Code:
      ```python
      {code_snippet}
      ```
      
      Provide only the corrected code without explanations.
      
  shell:
    system: "You are a shell scripting expert. Fix bash/shell script errors."
    error_template: |
      Fix this shell script error:
      
      Error: {error_message}
      
      Script:
      ```bash
      {code_snippet}
      ```
      
      Return only the fixed script.
```

## Użycie

### Podstawowe komendy
```bash
# Automatyczne wykrywanie języka
airun script.py
airun deploy.sh
airun server.js
airun api.php

# Z argumentami dla skryptu
airun backup.sh /home/user /backup/location
airun data_processor.py --input data.csv --output results.json

# Wymuszenie konkretnego interpretera
airun --lang=python mysterious_script.txt
airun --lang=shell commands.txt

# Użycie konkretnego LLM
airun --llm=ollama:codellama script.py
airun --llm=openai:gpt-4 complex_debug.js
airun --llm=claude:claude-3 data_analysis.py

# Wyłączenie auto-naprawiania
airun --no-fix potentially_dangerous.sh

# Użycie własnego pliku konfiguracyjnego  
airun --config ./project-config.yaml script.py
```

### Przykłady użycia

#### 1. Python script z błędem składniowym
```bash
# Plik: test.py
print("Hello World"
print("Missing parenthesis")

# Uruchomienie
airun test.py

# Output:
# Executing test.py (attempt 1/4)
# Error detected, attempting AI fix...
# AI suggests fix: Added missing closing parenthesis
# Applied AI fix, retrying...
# Executing test.py (attempt 2/4)
# Hello World
# Missing parenthesis
# Execution completed in 1.23s
```

#### 2. Shell script z problemami uprawnień
```bash
# Plik: setup.sh
#!/bin/bash
mkdir /opt/myapp
cp files/* /opt/myapp/

# Uruchomienie
airun setup.sh

# AI automatycznie doda sudo tam gdzie potrzeba
```

#### 3. JavaScript z błędami typu
```bash
# Plik: calc.js
function add(a, b) {
    return a + b;
}

console.log(add("5", 3)); // Type error

# AI zaproponuje konwersję typów
```

## Konfiguracja projektowa

Możesz tworzyć konfigurację per-projekt:

```yaml
# .airunner.yaml w katalogu projektu
default_llm: "ollama:codellama:13b"
auto_fix: true

runners:
  python:
    executable: "python3.11"
    flags: ["-u", "-X", "dev"]
    
  nodejs:
    executable: "node"
    flags: ["--experimental-modules", "--loader", "ts-node/esm"]

# Specjalne prompty dla tego projektu
prompts:
  python:
    system: "You are debugging a Django web application. Consider Django patterns and best practices."
```

## Rozszerzenia

### Dodawanie nowych interpreterów

```python
# W pliku airunner.py dodaj nową klasę:
class RustRunner(BaseRunner):
    def execute(self, script_path: str, args: List[str] = None) -> ExecutionResult:
        cmd = ['cargo', 'run', '--manifest-path', f'{script_path}/Cargo.toml']
        if args:
            cmd.extend(['--'] + args)
        return self._run_subprocess(cmd)

# Dodaj do mapowania w AIRunner.__init__:
self.runners[ScriptType.RUST] = RustRunner(self.config['runners'])
```

### Integracja z IDE

#### VS Code Extension (concept)
```json
{
  "contributes": {
    "commands": [
      {
        "command": "airunner.run",
        "title": "Run with AI Runner"
      }
    ],
    "keybindings": [
      {
        "command": "airunner.run",
        "key": "ctrl+f5"
      }
    ]
  }
}
```

### Webhook integration dla CI/CD

```yaml
# .github/workflows/ai-test.yml
name: AI-Enhanced Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup AI Runner
      run: |
        pip install -r requirements.txt
        ollama serve &
        ollama pull codellama:7b
    - name: Run tests with AI fixing
      run: airun test_suite.py --max-retries=1
```

## Monitoring i logi

AI Runner automatycznie tworzy logi w `~/.airunner/logs/`:

```
~/.airunner/
├── config.yaml
├── logs/
│   ├── executions.log
│   ├── fixes.log
│   └── errors.log
└── backups/
    ├── script.py.backup.2024-06-04-10-30
    └── deploy.sh.backup.2024-06-04-11-15
```

### Przykład wpisu w logach:
```json
{
  "timestamp": "2024-06-04T10:30:15Z",
  "script_path": "/home/user/test.py",
  "script_type": "python",
  "execution_time": 1.23,
  "exit_code": 0,
  "ai_fixes_applied": 1,
  "llm_provider": "ollama:codellama",
  "fix_confidence": 0.85
}
```

## Troubleshooting

### Częste problemy

1. **Ollama nie odpowiada**
```bash
# Sprawdź czy Ollama działa
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

2. **Model nie został pobrany**
```bash
# Lista dostępnych modeli
ollama list

# Pobierz model
ollama pull codellama:7b
```

3. **Błędy uprawnień**
```bash
# Dodaj uprawnienia do katalogu config
mkdir -p ~/.airunner
chmod 755 ~/.airunner
```

4. **Python dependencies**
```bash
# Zainstaluj wszystkie wymagane pakiety
pip install click pyyaml requests pathlib dataclasses asyncio
```

### Debug mode

```bash
# Uruchom z dodatkowymi logami
AIRUNNER_DEBUG=1 airun script.py

# Lub dodaj do config.yaml:
debug: true
verbose_output: true
```

## Performance Tips

1. **Używaj lżejszych modeli dla prostych błędów**
```yaml
llm_providers:
  ollama:
    models:
      python: "codellama:7b"  # szybszy
      shell: "mistral:7b"     # dla prostych skryptów
```

2. **Cache dla częstych błędów**
```yaml
error_fixing:
  cache_fixes: true
  cache_duration: 3600  # 1 godzina
```

3. **Timeout optymalizacja**
```yaml
timeout: 60  # dla szybkich skryptów
llm_timeout: 15  # limit dla LLM response
```

To rozwiązanie daje solidną podstawę do universal interpretera z AI error fixing. Możesz go rozbudowywać o dodatkowe języki, lepsze prompty, czy integracje z różnymi LLM providers.