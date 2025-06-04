#!/bin/bash
set -e

echo "🛠️  Setting up AIRun development environment..."

# Install Poetry
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
poetry install --with dev,test

# Setup pre-commit hooks
poetry run pre-commit install

# Create test directories
mkdir -p tests/fixtures/{scripts,configs,outputs}

# Setup example broken scripts for testing
cat > tests/fixtures/scripts/broken_python.py << 'EOF'
# Missing closing parenthesis
print("Hello World"
print("This will fail")

# Undefined variable
result = undefined_variable + 5
print(result)
EOF

cat > tests/fixtures/scripts/broken_shell.sh << 'EOF'
#!/bin/bash
# Missing quotes and undefined variable
echo Hello $UNDEFINED_VAR
mkdir /opt/test  # Permission error
EOF

cat > tests/fixtures/scripts/broken_node.js << 'EOF'
// Missing semicolon and undefined function
console.log("Starting")
undefinedFunction()
let result = 5 + "10"  // Type coercion issue
console.log(result)
EOF

# Run initial tests
echo "🧪 Running initial tests..."
poetry run pytest --tb=short

# Setup documentation
echo "📚 Setting up documentation..."
poetry run mkdocs new . --force
poetry run mkdocs build

echo "✅ Development environment ready!"
echo "🔧 Run 'poetry run airun --help' to test"
echo "📚 Run 'poetry run mkdocs serve' for docs"
echo "🧪 Run 'poetry run pytest' for tests"