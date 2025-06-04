#!/bin/bash
set -e

echo "🚀 Installing AIRun..."

# Check Python version
python3 -c "import sys; assert sys.version_info >= (3, 8)" || {
    echo "❌ Python 3.8+ required"
    exit 1
}

# Install Poetry if not present
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install AIRun
if [ -d "airun" ]; then
    cd airun
    poetry install
else
    echo "📥 Cloning AIRun repository..."
    git clone https://github.com/wronai/airun.git
    cd airun
    poetry install
fi

# Setup configuration directory
mkdir -p ~/.airun/{logs,backups,cache}

# Install default config if not exists
if [ ! -f ~/.airun/config.yaml ]; then
    echo "⚙️  Installing default configuration..."
    poetry run python -c "
from airun.core.config import create_default_config
create_default_config()
"
fi

echo "✅ AIRun installed successfully!"
echo "📖 Run 'airun --help' to get started"
echo "🔧 Run 'airun-doctor' to check your setup"