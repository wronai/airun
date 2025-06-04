#!/bin/bash
set -e

echo "🦙 Setting up Ollama for AIRun..."

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Download recommended models
echo "📥 Downloading Code Llama models..."
ollama pull codellama:7b
ollama pull codellama:13b

echo "📥 Downloading Mistral for shell scripts..."
ollama pull mistral:7b

# Test models
echo "🧪 Testing models..."
echo "print('Hello from AI!')" | ollama run codellama:7b "Fix this Python code:"

echo "✅ Ollama setup complete!"
echo "🔧 Models available: codellama:7b, codellama:13b, mistral:7b"

# Update AIRun config to use these models
poetry run python -c "
from airun.core.config import update_ollama_models
update_ollama_models(['codellama:7b', 'codellama:13b', 'mistral:7b'])
"

echo "⚙️  AIRun configuration updated!"