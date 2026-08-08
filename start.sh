#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — One-command launcher for Puzzle Generator
#
# Usage:
#   chmod +x start.sh
#   ./start.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

PYTHON=""

# Prefer Homebrew Python 3.11 (installed by this project setup)
if command -v /opt/homebrew/bin/python3.11 &>/dev/null; then
  PYTHON=/opt/homebrew/bin/python3.11
elif command -v python3.11 &>/dev/null; then
  PYTHON=python3.11
elif command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "❌  Python not found. Install Python 3.9+ and retry."
  exit 1
fi

echo "🐍  Using Python: $($PYTHON --version)"

# Install / upgrade dependencies
echo "📦  Installing dependencies..."
"$PYTHON" -m pip install -r requirements.txt --quiet

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🧩  Puzzle Generator — starting FastAPI server...  ║"
echo "║  Open your browser at: http://localhost:8000         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

"$PYTHON" server.py
