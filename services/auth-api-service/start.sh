#!/bin/bash
set -e

echo "🚀 Starting Auth API Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from example..."
    cp .env.example .env
    echo "✏️ Please update .env file with your configuration"
fi

# Start the service
echo "🎯 Starting Auth API Service on port 8085..."
echo "📋 API Documentation: http://localhost:8085/docs"
echo "🔍 Health Check: http://localhost:8085/api/auth/health"
echo ""

python src/main.py
