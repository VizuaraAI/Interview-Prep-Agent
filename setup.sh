#!/bin/bash

echo "================================"
echo "ML Interview Agent - Part 1 Setup"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

# Setup Backend
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "✅ Backend setup complete"

cd ..

# Setup Frontend
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo "Node modules already installed"
fi

echo "✅ Frontend setup complete"

cd ..

# Final instructions
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "⚠️  IMPORTANT: Before starting, make sure to:"
echo "1. Run the SQL schema in Supabase (backend/schema.sql)"
echo "2. Add your Supabase anon key to backend/.env"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "See SETUP_GUIDE.md for detailed instructions"
