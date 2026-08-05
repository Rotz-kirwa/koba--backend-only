#!/bin/bash

echo "=========================================="
echo "  QUEEN KOBA SYSTEM DIAGNOSTICS"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check MongoDB
echo "1. Checking MongoDB..."
if systemctl is-active --quiet mongodb; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB is not running${NC}"
    echo "  Starting MongoDB..."
    sudo systemctl start mongodb
fi
echo ""

# Check Backend
echo "2. Checking Backend (Port 5000)..."
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Backend is running on port 5000${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "  To start: cd backend/queen-koba-backend && python3 queenkoba_mongodb.py"
fi
echo ""

# Check Frontend
echo "3. Checking Frontend (Port 8080)..."
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Frontend is running on port 8080${NC}"
else
    echo -e "${RED}✗ Frontend is not running${NC}"
    echo "  To start: cd frontend && npm run dev"
fi
echo ""

# Check Admin
echo "4. Checking Admin (Port 3001)..."
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Admin is running on port 3001${NC}"
else
    echo -e "${RED}✗ Admin is not running${NC}"
    echo "  To start: cd admin && npm run dev"
fi
echo ""

# Check Environment Files
echo "5. Checking Environment Files..."
if [ -f "frontend/.env" ]; then
    echo -e "${GREEN}✓ Frontend .env exists${NC}"
else
    echo -e "${RED}✗ Frontend .env missing${NC}"
fi

if [ -f "admin/.env" ]; then
    echo -e "${GREEN}✓ Admin .env exists${NC}"
else
    echo -e "${RED}✗ Admin .env missing${NC}"
fi

if [ -f "backend/queen-koba-backend/.env" ]; then
    echo -e "${GREEN}✓ Backend .env exists${NC}"
else
    echo -e "${RED}✗ Backend .env missing${NC}"
fi
echo ""

# Test Backend API
echo "6. Testing Backend API..."
if curl -s http://localhost:5000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is responding${NC}"
else
    echo -e "${RED}✗ Backend API is not responding${NC}"
fi
echo ""

# Check MongoDB Connection
echo "7. Testing MongoDB Connection..."
if mongo --eval "db.adminCommand('ping')" queenkoba > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MongoDB connection successful${NC}"
else
    echo -e "${RED}✗ MongoDB connection failed${NC}"
fi
echo ""

# Check Collections
echo "8. Checking MongoDB Collections..."
echo "   Products: $(mongo queenkoba --quiet --eval 'db.products.count()')"
echo "   Users: $(mongo queenkoba --quiet --eval 'db.users.count()')"
echo "   Orders: $(mongo queenkoba --quiet --eval 'db.orders.count()')"
echo "   Promotions: $(mongo queenkoba --quiet --eval 'db.promotions.count()')"
echo "   Reviews: $(mongo queenkoba --quiet --eval 'db.reviews.count()')"
echo "   Support Tickets: $(mongo queenkoba --quiet --eval 'db.support_tickets.count()')"
echo ""

echo "=========================================="
echo "  DIAGNOSTICS COMPLETE"
echo "=========================================="
echo ""
echo "Quick Start Commands:"
echo "  Backend:  cd backend/queen-koba-backend && python3 queenkoba_mongodb.py"
echo "  Frontend: cd frontend && npm run dev"
echo "  Admin:    cd admin && npm run dev"
echo ""
