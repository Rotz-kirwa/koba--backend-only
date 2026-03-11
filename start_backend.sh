#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🚀 Starting Queen Koba Backend API (PostgreSQL)..."
if [ -x "venv/bin/python" ]; then
  venv/bin/python queenkoba_postgresql.py
else
  python3 queenkoba_postgresql.py
fi
