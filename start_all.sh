#!/bin/bash

echo "=========================================="
echo "  QUEEN KOBA E-COMMERCE SYSTEM"
echo "  Complete Startup Script"
echo "=========================================="
echo ""

# Check if MongoDB is running
echo "1. Checking MongoDB..."
if systemctl is-active --quiet mongodb; then
    echo "✓ MongoDB is running"
else
    echo "✗ MongoDB is not running. Starting..."
    sudo systemctl start mongodb
    sleep 2
fi
echo ""

# Start Backend
echo "2. Starting Backend API (Port 5000)..."
cd /home/user/Public/koba/backend/queen-koba-backend
python3 queenkoba_mongodb.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
sleep 3
echo ""

# Start Frontend
echo "3. Starting Frontend (Port 8080)..."
cd /home/user/Public/koba/frontend
npm run dev -- --port 8080 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"
sleep 3
echo ""

# Start Admin
echo "4. Starting Admin Dashboard (Port 3001)..."
cd /home/user/Public/koba/admin
npm run dev -- --port 3001 &
ADMIN_PID=$!
echo "✓ Admin started (PID: $ADMIN_PID)"
sleep 3
echo ""

echo "=========================================="
echo "  ALL SERVICES STARTED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  Frontend:  http://localhost:8080"
echo "  Backend:   http://localhost:5000"
echo "  Admin:     http://localhost:3001"
echo ""
echo "Admin Credentials:"
echo "  Email:     admin@queenkoba.com"
echo "  Password:  admin123"
echo ""
echo "Process IDs:"
echo "  Backend:   $BACKEND_PID"
echo "  Frontend:  $FRONTEND_PID"
echo "  Admin:     $ADMIN_PID"
echo ""
echo "To stop all services:"
echo "  kill $BACKEND_PID $FRONTEND_PID $ADMIN_PID"
echo ""
echo "Press Ctrl+C to stop all services..."
echo "=========================================="

# Wait for user interrupt
wait
