#!/usr/bin/env bash
set -euo pipefail

# TraceRail Bootstrap Environment Setup Script

echo "🚀 TraceRail Bootstrap Environment Setup"
echo "========================================"

# Check if .env already exists
if [ -f .env ]; then
    echo "📝 .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "ℹ️  Setup cancelled. Edit .env manually if needed."
        exit 0
    fi
fi

# Copy the example file
echo "📋 Creating .env from .env.example..."
cp .env.example .env

# Check for LLM API key
echo ""
echo "🔑 LLM API Key Setup"
echo "-------------------"
echo "To use real AI responses, you need an API key."
echo "Options:"
echo "  1. DeepSeek (recommended - more cost effective)"
echo "     Get one at: https://platform.deepseek.com/api_keys"
echo "  2. OpenAI"
echo "     Get one at: https://platform.openai.com/api-keys"
echo ""

read -p "Which API do you want to use? (1=DeepSeek, 2=OpenAI, N=skip): " api_choice

case $api_choice in
    1)
        echo ""
        read -p "Enter your DeepSeek API key: " api_key
        if [ -n "$api_key" ]; then
            # Update the .env file with the DeepSeek API key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/DEEPSEEK_API_KEY=your-deepseek-api-key-here/DEEPSEEK_API_KEY=$api_key/" .env
            else
                # Linux
                sed -i "s/DEEPSEEK_API_KEY=your-deepseek-api-key-here/DEEPSEEK_API_KEY=$api_key/" .env
            fi
            echo "✅ DeepSeek API key configured!"
        else
            echo "⚠️  No API key entered. You can edit .env later."
        fi
        ;;
    2)
        echo ""
        read -p "Enter your OpenAI API key: " api_key
        if [ -n "$api_key" ]; then
            # Update the .env file with the OpenAI API key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/OPENAI_API_KEY=your-openai-api-key-here/OPENAI_API_KEY=$api_key/" .env
            else
                # Linux
                sed -i "s/OPENAI_API_KEY=your-openai-api-key-here/OPENAI_API_KEY=$api_key/" .env
            fi
            echo "✅ OpenAI API key configured!"
        else
            echo "⚠️  No API key entered. You can edit .env later."
        fi
        ;;
    *)
        echo "ℹ️  Skipping API key setup."
        echo "   The system will use mock responses for testing."
        echo "   You can add your API key to .env later."
        ;;
esac

echo ""
echo "🐍 Python Environment Setup"
echo "---------------------------"

# Check if pyenv is available
if command -v pyenv &> /dev/null; then
    echo "✅ pyenv found"

    # Check if Python 3.12.8 is installed
    if pyenv versions | grep -q "3.12.8"; then
        echo "✅ Python 3.12.8 is installed"
    else
        echo "📦 Installing Python 3.12.8..."
        pyenv install 3.12.8
    fi

    # Set local Python version
    echo "🔧 Setting local Python version to 3.12.8..."
    pyenv local 3.12.8
else
    echo "⚠️  pyenv not found. Please install Python 3.12 manually."
    echo "   Visit: https://github.com/pyenv/pyenv#installation"
fi

# Check if poetry is available
if command -v poetry &> /dev/null; then
    echo "✅ Poetry found"

    # Configure poetry to use pyenv python if available
    if command -v pyenv &> /dev/null; then
        echo "🔧 Configuring Poetry to use pyenv Python..."
        poetry env use $(pyenv which python)
    fi

    echo "📦 Installing Python dependencies..."
    poetry install --with dev

    echo "✅ Dependencies installed!"
else
    echo "⚠️  Poetry not found. Please install Poetry first."
    echo "   Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo ""
echo "🐳 Docker Services"
echo "-----------------"

# Check if Docker is running
if docker info &> /dev/null; then
    echo "✅ Docker is running"

    read -p "Start Docker services now? (Y/n): " start_docker
    if [[ ! $start_docker =~ ^[Nn]$ ]]; then
        echo "🚀 Starting Docker services..."
        make dev
        echo "✅ Docker services started!"
    fi
else
    echo "⚠️  Docker is not running. Please start Docker first."
    echo "   Run 'make dev' when Docker is ready."
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Start the worker:     make worker"
echo "2. Run a workflow:       poetry run python cli/start_example.py 'hello world'"
echo ""
echo "Web interfaces:"
echo "• Temporal UI:    http://localhost:8233"
echo "• Flowable DMN:   http://localhost:8082/flowable-rest/docs/"
echo "• Task Bridge:    http://localhost:7070/docs"
echo "• Grafana:        http://localhost:3000 (admin/grafana)"
echo ""
echo "Configuration file: .env"
echo ""
