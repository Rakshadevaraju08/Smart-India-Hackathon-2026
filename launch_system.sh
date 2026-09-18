#!/usr/bin/env bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "======================================================================"
echo "   KAIROS COMMAND TWIN - URBAN FLOOD NOWCASTING SYSTEM (SIH 2026)"
echo "   Ministry of Earth Sciences (MoES) / NCMRWF | Chennai Pilot #26085"
echo "======================================================================"

echo "[1/2] Starting Node.js API Gateway & WebSocket Hub..."
cd "$SCRIPT_DIR/backend"
npm start &
BACKEND_PID=$!

echo "[2/2] Launching Web GIS Command Dashboard in default browser..."
sleep 1
if command -v xdg-open &> /dev/null; then
    xdg-open "http://127.0.0.1:5000" || xdg-open "$SCRIPT_DIR/frontend/index.html"
elif command -v open &> /dev/null; then
    open "http://127.0.0.1:5000" || open "$SCRIPT_DIR/frontend/index.html"
fi

echo "======================================================================"
echo "  KAIROS System Operational!"
echo "  Backend PID: $BACKEND_PID"
echo "  Press Ctrl+C to terminate."
echo "======================================================================"

wait $BACKEND_PID
