# Queen Koba E-Commerce Platform

Complete e-commerce solution for Queen Koba skincare products.

## Project Structure

```
koba/
├── frontend/          # Customer-facing store (React + Vite)
├── backend/           # Backend API (Flask + MongoDB)
└── admin/            # Admin dashboard
```

## Services

- **Frontend**: http://localhost:8080
- **Backend**: http://localhost:5000
- **Admin**: http://localhost:3001

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend/queen-koba-backend

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt

# Create .env file with your MongoDB URI and secrets

# Start MongoDB
sudo systemctl start mongodb
# OR
docker run -d --name queenkoba-mongodb -p 27017:27017 mongo:latest

# Run backend
python queenkoba_mongodb.py
```

### Admin

```bash
cd admin
npm install
npm run dev
```

## Technologies

This project is built with:

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn-ui
- **Backend**: Flask, MongoDB, Python
- **Admin**: React, TypeScript, Vite

## Contact

- Email: info@queenkoba.com
- Phone: 0119 559 180
- WhatsApp: 0119 559 180
- Instagram: @queenkoba
