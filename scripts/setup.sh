#!/bin/bash
# Finsight AI — Quick local setup script

set -e

echo "🚀 Setting up Finsight AI..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required"; exit 1; }
command -v redis-server >/dev/null 2>&1 || { echo "Redis required (brew install redis)"; exit 1; }

# Backend
echo "\n📦 Installing backend dependencies..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Frontend
echo "\n📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Env files
if [ ! -f .env ]; then
  cp .env.example .env
  echo "\n⚠️  Created .env from .env.example — fill in your API keys!"
fi

if [ ! -f frontend/.env.local ]; then
  cat > frontend/.env.local << 'EOF'
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_API_URL=https://localhost:8000/api/v1
EOF
  echo "⚠️  Created frontend/.env.local — fill in Clerk credentials!"
fi

echo "\n✅ Setup complete!"
echo "\nTo start development:"
echo "  Terminal 1: redis-server"
echo "  Terminal 2: ./start.sh"
