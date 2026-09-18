#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Risk2Relief: Initializing Developer Environment   "
echo "=================================================="

# 1. Check Python
echo -e "\n[1/4] Checking Python 3.12+..."
python3 --version || python --version

# 2. Check Node
echo -e "\n[2/4] Checking Node.js & npm..."
node -v
npm -v

# 3. Setup Frontend dependencies
echo -e "\n[3/4] Installing Frontend Dependencies..."
cd frontend && npm install && cd ..

# 4. Copy environment template if not exists
echo -e "\n[4/4] Configuring Environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
else
    echo ".env already exists, skipping."
fi

echo -e "\n=================================================="
echo " Environment initialized successfully!           "
echo " Run 'docker compose up' or local dev servers.   "
echo "=================================================="
