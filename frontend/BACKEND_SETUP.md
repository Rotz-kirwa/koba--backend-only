# Queen Koba - Backend Setup Instructions

## Backend Location
The backend is cloned at: `/home/user/Public/queen-koba-backend`

## Quick Start

### 1. Install Python Virtual Environment (if not installed)
```bash
sudo apt install python3.12-venv
```

### 2. Navigate to Backend Directory
```bash
cd /home/user/Public/queen-koba-backend
```

### 3. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r queen-koba-backend/app/requirements.txt
```

### 5. Start MongoDB (Choose one option)

**Option A: Local MongoDB**
```bash
sudo systemctl start mongodb
```

**Option B: Docker**
```bash
docker run -d --name queenkoba-mongodb -p 27017:27017 mongo:latest
```

### 6. Configure Environment
Create `.env` file in the backend root:
```bash
cat > .env << 'EOF'
MONGO_URI=mongodb://localhost:27017/queenkoba
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=86400
FLASK_APP=queenkoba_mongodb.py
FLASK_ENV=development
SECRET_KEY=your-flask-secret-key-change-in-production
EOF
```

### 7. Run the Backend
```bash
cd queen-koba-backend
python queenkoba_mongodb.py
```

The backend will run on: `http://localhost:5000`

## Frontend Connection

The frontend is already configured to connect to the backend at `http://localhost:5000`.

Configuration file: `/home/user/Public/royal-melanin-glow/.env`

API service: `/home/user/Public/royal-melanin-glow/src/lib/api.ts`

## Testing the Connection

### 1. Start the Backend (Terminal 1)
```bash
cd /home/user/Public/queen-koba-backend
source venv/bin/activate
python queen-koba-backend/queenkoba_mongodb.py
```

### 2. Start the Frontend (Terminal 2)
```bash
cd /home/user/Public/royal-melanin-glow
npm run dev
```

### 3. Test API Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Get products
curl http://localhost:5000/products

# Register user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@queenkoba.com",
    "password": "test123",
    "country": "Kenya",
    "preferred_currency": "KES"
  }'
```

## Default Admin Credentials
- Email: `admin@queenkoba.com`
- Password: `admin123`

⚠️ **Change these in production!**

## API Endpoints

### Public Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /products` - List all products
- `GET /products/{id}` - Get single product
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /payment-methods/{country}` - Payment methods by country

### Protected Endpoints (Require JWT Token)
- `GET /auth/profile` - Get user profile
- `GET /cart` - View user's cart
- `POST /cart/add` - Add item to cart
- `DELETE /cart/remove/{id}` - Remove item from cart
- `POST /checkout` - Create order from cart
- `GET /orders` - Get user's orders
- `GET /orders/{id}` - Get specific order

## Troubleshooting

### MongoDB Connection Failed
```bash
# Start MongoDB
sudo systemctl start mongodb

# Or with Docker
docker start queenkoba-mongodb
```

### Port 5000 Already in Use
```bash
# Kill process on port 5000
sudo fuser -k 5000/tcp
```

### Module Import Errors
```bash
# Reinstall requirements
pip install -r queen-koba-backend/app/requirements.txt
```

## Project Structure
```
/home/user/Public/
├── royal-melanin-glow/          # Frontend (React + Vite)
│   ├── src/
│   │   └── lib/
│   │       └── api.ts           # API service
│   ├── .env                     # Frontend environment config
│   └── package.json
│
└── queen-koba-backend/          # Backend (Flask + MongoDB)
    ├── queen-koba-backend/
    │   ├── queenkoba_mongodb.py # Main application
    │   └── app/
    │       └── requirements.txt
    ├── .env                     # Backend environment config
    └── venv/                    # Python virtual environment
```

## Next Steps

1. Install python3-venv: `sudo apt install python3.12-venv`
2. Set up MongoDB (local or Docker)
3. Create backend virtual environment
4. Install backend dependencies
5. Configure `.env` files
6. Start backend server
7. Start frontend dev server
8. Test the connection

For detailed backend documentation, see: `/home/user/Public/queen-koba-backend/README.md`
