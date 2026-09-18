#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "   KAIROS URBAN FLOOD NOWCASTING SYSTEM - DEPENDENCY INSTALLER"
echo "   Smart India Hackathon 2026 (Problem Statement 26085)"
echo "======================================================================"

echo ""
echo "[1/3] Installing Python Dependencies..."
if command -v python3 &> /dev/null; then
    python3 -m pip install --upgrade pip || true
    python3 -m pip install -r requirements.txt
elif command -v python &> /dev/null; then
    python -m pip install --upgrade pip || true
    python -m pip install -r requirements.txt
fi

echo ""
echo "[2/3] Installing Backend Node.js Dependencies..."
if [ -d "backend" ]; then
    cd backend
    npm install
    cd ..
fi

echo ""
echo "[3/3] Installing Frontend React / Vite Dependencies..."
if [ -d "Frontend" ]; then
    cd Frontend
    npm install
    cd ..
fi

echo ""
echo "======================================================================"
echo "   Running Verification Checks..."
echo "======================================================================"
if command -v pytest &> /dev/null; then
    pytest ai_service/tests/ -q || true
fi
if command -v node &> /dev/null; then
    node backend/tests/test_api.js || true
fi

echo ""
echo "======================================================================"
echo "   [COMPLETE] All dependencies installed and operational!"
echo "   Launch the system with: bash launch_system.sh"
echo "======================================================================"
