#!/bin/bash

cd /home/user/Public/koba/backend/queen-koba-backend

# Activate virtual environment
source venv/bin/activate

# Start the backend
echo "🚀 Starting Queen Koba Backend API..."
python queenkoba_mongodb.py
