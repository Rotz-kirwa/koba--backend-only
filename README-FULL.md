# Royal Melanin Glow (Queen Koba)

Complete e-commerce platform for Queen Koba skincare products.

## Project Structure

```
royal-melanin-glow/
├── src/                    # Frontend source (Customer Store)
├── admin-dashboard/        # Admin Dashboard
├── backend/               # Backend API (Flask + MongoDB)
├── public/                # Frontend public assets
├── package.json           # Frontend dependencies
└── README.md
```

## Services

- **Frontend (Customer Store)**: http://localhost:8080
- **Admin Dashboard**: http://localhost:3001
- **Backend API**: http://localhost:5000

## Quick Start

### 1. Frontend (Customer Store)

```bash
cd /home/user/Public/royal-melanin-glow
npm install
npm run dev
```

Runs on: http://localhost:8080

### 2. Admin Dashboard

```bash
cd /home/user/Public/royal-melanin-glow/admin-dashboard
npm install
npm run dev
```

Runs on: http://localhost:3001

### 3. Backend API

**Setup:**
```bash
cd /home/user/Public/royal-melanin-glow/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r queen-koba-backend/app/requirements.txt

# Create .env file
cat > .env << 'EOF'
MONGO_URI=mongodb://localhost:27017/queenkoba
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ACCESS_TOKEN_EXPIRES=86400
FLASK_APP=queenkoba_mongodb.py
FLASK_ENV=development
SECRET_KEY=your-flask-secret-key
EOF
```

**Start MongoDB:**
```bash
# Option A: Local
sudo systemctl start mongodb

# Option B: Docker
docker run -d --name queenkoba-mongodb -p 27017:27017 mongo:latest
```

**Run Backend:**
```bash
cd /home/user/Public/royal-melanin-glow/backend
source venv/bin/activate
python queen-koba-backend/queenkoba_mongodb.py
```

Runs on: http://localhost:5000

## Features

### Customer Store (Frontend)
- Product catalog (6 products)
- Shopping cart
- 4-step checkout process
- 13 payment methods (4 countries)
- Currency conversion (KES, UGX, BIF, CDF)
- WhatsApp integration
- Contact form

### Admin Dashboard
- Dashboard statistics
- Orders management
- Products CRUD
- Users management
- Payments tracking
- Mobile responsive

### Backend API
- JWT authentication
- Product management
- Cart operations
- Order processing
- Payment methods by country
- Admin endpoints

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Admin**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: Python Flask, MongoDB, JWT

## Contact Information

- Email: info@queenkoba.com
- Phone: 0119 559 180
- WhatsApp: 0119 559 180
- Instagram: @queenkoba

## Default Admin Credentials

- Email: `admin@queenkoba.com`
- Password: `admin123`

⚠️ **Change in production!**

## Development

Each part can be developed independently:

```bash
# Frontend only
cd /home/user/Public/royal-melanin-glow
npm run dev

# Admin only
cd /home/user/Public/royal-melanin-glow/admin-dashboard
npm run dev

# Backend only
cd /home/user/Public/royal-melanin-glow/backend
source venv/bin/activate
python queen-koba-backend/queenkoba_mongodb.py
```

## Deployment

- **Frontend**: See VERCEL_DEPLOYMENT.md
- **Admin**: Deploy to Vercel/Netlify
- **Backend**: Deploy to Heroku/Railway/DigitalOcean
