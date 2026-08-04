                                                   QUEEN KOBA SKINCARE API INSTALLATION GUIDE 


🧴 Queen Koba Skincare API
A complete RESTful API backend for Queen Koba Skincare e-commerce platform, featuring multi-currency pricing, user authentication, shopping cart functionality, and order management for East African markets.

📋 Table of Contents
Features

Tech Stack

Installation

Configuration

API Endpoints

Database Schema

Usage Examples

Testing

Deployment

Contributing

License

🛍️ Core Features
Multi-Currency Pricing: Products priced in Kenyan Shilling (KES), Ugandan Shilling (UGX), Burundi Franc (BIF), and Congolese Franc (CDF)

User Management: Secure registration, login, and profile management with JWT authentication

Shopping Cart: Add, remove, and update items in cart with real-time price calculation

Order Processing: Complete checkout flow with order history tracking

Payment Methods: Country-specific payment options for East Africa

💱 Supported Currencies
Currency	Code	Symbol	Country
Kenyan Shilling	KES	KSh	Kenya
Ugandan Shilling	UGX	USh	Uganda
Burundi Franc	BIF	FBu	Burundi
Congolese Franc	CDF	FC	DRC Congo

💳 Payment Methods by Country
Kenya: M-Pesa, Airtel Money, Visa/Mastercard, Bank Transfer

Uganda: MTN Mobile Money, Airtel Money, Visa/Mastercard

Burundi: Lumicash, EcoCash, Bank Transfer

DRC Congo: Orange Money, Vodacom M-Pesa, Bank Transfer

🛠️ Tech Stack
Backend
Python 3.8+ - Primary programming language

Flask - Lightweight web framework

Flask-PyMongo - MongoDB integration

Flask-JWT-Extended - Authentication & authorization

Flask-CORS - Cross-Origin Resource Sharing

bcrypt - Password hashing

python-dotenv - Environment configuration

Database
MongoDB - NoSQL database for flexible data storage

MongoDB Atlas (optional) - Cloud database service
Development & Testing
Postman / cURL - API testing

Docker (optional) - Containerized MongoDB

Gunicorn - Production WSGI server

🚀 Installation
Prerequisites
Python 3.8 or higher

MongoDB (local installation or Docker)

pip (Python package manager)

Git

Step 1: Clone the Repository
git clone https://github.com/macharia80/queen-koba-backend.git
cd queen-koba-backend/queen-koba-backend/queen-koba-backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

Step 3: Install Dependencies
pip install -r requirements.txt

If requirements.txt doesn't exist, install manually:

pip install Flask==2.3.3 Flask-CORS==4.0.0 pymongo==4.5.0
pip install Flask-PyMongo==2.3.0 Flask-JWT-Extended==4.5.3
pip install bcrypt==4.1.2 python-dotenv==1.0.0

Step 4: Set Up MongoDB
Option A: Local MongoDB Installation
# On Ubuntu/Debian
sudo apt update
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Check MongoDB status
sudo systemctl status mongodb

Option B: Docker (Recommended)
# Pull and run MongoDB container
docker run -d \
  --name queenkoba-mongodb \
  -p 27017:27017 \
  -v queenkoba-data:/data/db \
  mongo:latest

# Check if MongoDB is running
docker ps | grep mongodb

Option C: MongoDB Atlas (Cloud)
Go to MongoDB Atlas

Create a free cluster

Get your connection string

Update .env file with Atlas connection string

Step 5: Configure Environment

# Create .env file
cat > .env << 'EOF'
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/queenkoba
# For MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/queenkoba

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours in seconds

# Flask Configuration
FLASK_APP=queenkoba_mongodb.py
FLASK_ENV=development
SECRET_KEY=your-flask-secret-key-change-in-production
EOF
⚠️ Security Note: Change the secret keys before deploying to production!

Step 6: Run the Application

# Activate virtual environment
source venv/bin/activate

# Start the Flask development server
python queenkoba_mongodb.py

You should see output like:
🚀 QUEEN KOBA SKINCARE API - MONGODB EDITION
✅ Connected to MongoDB
✅ Seeded 6 products
✅ Created admin user: admin@queenkoba.com / N/A
 * Running on http://0.0.0.0:5000

Step 7: Verify Installation
Open a new terminal and test:
# Test API is running
curl http://localhost:5000/

# Test health endpoint
curl http://localhost:5000/health

# Test products endpoint
curl http://localhost:5000/products

⚙️ Configuration
Environment Variables
Create a .env file in the root directory:
# Required
MONGO_URI=mongodb://localhost:27017/queenkoba
JWT_SECRET_KEY=your-secret-key-here

# Optional
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000
HOST=0.0.0.0

# CORS Settings (for frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

Admin Credentials
Default admin user is automatically created:

Email: admin@queenkoba.com

Password: admin123

⚠️ Important: Change the default admin password in production!


📡 API Endpoints
Public Endpoints
Method	Endpoint	Description	Authentication
GET	/	API information	❌
GET	/health	Health check	❌
GET	/products	List all products	❌
GET	/products/{id}	Get single product	❌
POST	/auth/register	Register new user	❌
POST	/auth/login	Login user	❌
GET	/payment-methods/{country}	Payment methods by country	❌
Protected Endpoints (Require JWT Token)
Method	Endpoint	Description
GET	/auth/profile	Get user profile
GET	/cart	View user's cart
POST	/cart/add	Add item to cart
DELETE	/cart/remove/{id}	Remove item from cart
POST	/checkout	Create order from cart
GET	/orders	Get user's orders
GET	/orders/{id}	Get specific order
Request/Response Examples
Register User
bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "country": "Kenya",
    "preferred_currency": "KES"
  }'
Response:

json
{
  "status": "success",
  "message": "Registration successful",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "_id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "country": "Kenya",
    "preferred_currency": "KES",
    "role": "customer"
  }
}
Login
bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@queenkoba.com",
    "password": "admin123"
  }'
Get Products
bash
curl http://localhost:5000/products
Sample Product Response:

json
{
  "status": "success",
  "count": 6,
  "products": [
    {
      "_id": "60d5ec9f4f1a2c001f8e4b5a",
      "name": "Complex Clarifier Cream",
      "description": "A luxurious cream that gently clarifies...",
      "base_price_usd": 29.99,
      "category": "Cream",
      "in_stock": true,
      "prices": {
        "KES": {
          "amount": 3850,
          "symbol": "KSh",
          "country": "Kenya"
        },
        "UGX": {
          "amount": 107400,
          "symbol": "USh",
          "country": "Uganda"
        }
      }
    }
  ]
}
Add to Cart (Authenticated)
bash
curl -X POST http://localhost:5000/cart/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "product_id": "60d5ec9f4f1a2c001f8e4b5a",
    "quantity": 2
  }'
🗃️ Database Schema
Products Collection
javascript
{
  "_id": ObjectId,
  "name": String,
  "description": String,
  "base_price_usd": Number,
  "category": String, // "Cream", "Serum", "Mask", etc.
  "in_stock": Boolean,
  "image_url": String,
  "prices": {
    "KES": {
      "amount": Number,
      "symbol": "KSh",
      "country": "Kenya"
    },
    "UGX": { ... },
    "BIF": { ... },
    "CDF": { ... }
  },
  "created_at": ISODate
}
Users Collection
javascript
{
  "_id": ObjectId,
  "username": String,
  "email": String,
  "password_hash": String, // bcrypt hashed
  "country": String,
  "preferred_currency": String, // "KES", "UGX", etc.
  "role": String, // "admin" or "customer"
  "cart": [
    {
      "product_id": ObjectId,
      "quantity": Number,
      "added_at": ISODate
    }
  ],
  "orders": [ObjectId], // References to orders
  "created_at": ISODate,
  "updated_at": ISODate
}
Orders Collection
javascript
{
  "_id": ObjectId,
  "order_id": String, // Human-readable ID like "QK123456"
  "user_id": ObjectId,
  "items": [
    {
      "product_id": ObjectId,
      "product_name": String,
      "quantity": Number,
      "price_per_item": Number,
      "item_total": Number
    }
  ],
  "total_usd": Number,
  "shipping_address": Object,
  "payment_method": String,
  "payment_status": String, // "pending", "completed", "failed"
  "order_status": String, // "processing", "shipped", "delivered"
  "created_at": ISODate,
  "updated_at": ISODate
}
🧪 Testing
Manual Testing with cURL
bash
# Test script
cat > test_api.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing Queen Koba API"

API="http://localhost:5000"

echo "1. Health check..."
curl -s $API/health | python3 -m json.tool

echo -e "\n2. Get products..."
curl -s $API/products | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Found {data[\"count\"]} products')
for p in data['products'][:2]:
    print(f'• {p[\"name\"]}: ${p[\"base_price_usd\"]}')
    print(f'  KES: {p[\"prices\"][\"KES\"][\"amount\"]} {p[\"prices\"][\"KES\"][\"symbol\"]}')
"

echo -e "\n3. Register test user..."
curl -s -X POST $API/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@queenkoba.com",
    "password": "test123",
    "country": "Kenya"
  }' | python3 -m json.tool

echo -e "\n✅ Tests completed!"
EOF

chmod +x test_api.sh
./test_api.sh
Python Test Script
python
import requests
import json

API = "http://localhost:5000"

def test_all_endpoints():
    print("Testing Queen Koba API Endpoints")
    print("="*40)
    
    # 1. Health check
    response = requests.get(f"{API}/health")
    print(f"1. Health: {response.status_code}")
    
    # 2. Get products
    response = requests.get(f"{API}/products")
    data = response.json()
    print(f"2. Products: {data['count']} items")
    
    # 3. Register user
    user_data = {
        "username": "test_user",
        "email": "test@email.com",
        "password": "password123",
        "country": "Kenya"
    }
    response = requests.post(f"{API}/auth/register", json=user_data)
    print(f"3. Register: {response.status_code}")
    
    # 4. Login
    login_data = {"email": "admin@queenkoba.com", "password": "admin123"}
    response = requests.post(f"{API}/auth/login", json=login_data)
    print(f"4. Login: {response.status_code}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_all_endpoints()
Using Postman
Import the Postman collection from postman_collection.json

Set environment variables:

base_url: http://localhost:5000

admin_token: (Get from login response)

Run the collection tests

🚢 Deployment
Production Deployment with Gunicorn
bash
# Install Gunicorn
pip install gunicorn

# Create requirements.txt
pip freeze > requirements.txt

# Create Procfile
echo "web: gunicorn --bind 0.0.0.0:\$PORT queenkoba_mongodb:app" > Procfile

# Run with Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 queenkoba_mongodb:app
Docker Deployment
dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MONGO_URI=mongodb://mongodb:27017/queenkoba
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "queenkoba_mongodb:app"]
yaml
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    container_name: queenkoba-mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
  
  api:
    build: .
    container_name: queenkoba-api
    restart: always
    ports:
      - "5000:5000"
    environment:
      MONGO_URI: mongodb://mongodb:27017/queenkoba
      JWT_SECRET_KEY: your-production-secret-key
    depends_on:
      - mongodb

volumes:
  mongodb_data:
Deploy to Cloud Platforms
Heroku
bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create queenkoba-api

# Add MongoDB addon
heroku addons:create mongolab:sandbox

# Deploy
git push heroku main

# Set environment variables
heroku config:set JWT_SECRET_KEY=your-secret-key
AWS Elastic Beanstalk
bash
# Initialize EB
eb init -p python-3.8 queenkoba-api

# Create environment
eb create queenkoba-api-env

# Set environment variables
eb setenv MONGO_URI=your-mongodb-uri JWT_SECRET_KEY=your-secret-key

# Deploy
eb deploy
📊 Sample Data
Products Available
Complex Clarifier Cream - $29.99 (KES 3,850)

Complexion Clarifier Serum - $34.50 (KES 4,430)

Complexion Clarifying Mask - $25.75 (KES 3,308)

Complexion Renewal Scrub - $21.99 (KES 2,825)

Rich Gentle Foaming Lather - $18.50 (KES 2,377)

Eternal Radiance Toner - $23.25 (KES 2,987)

Exchange Rates
USD to KES: 128.5

USD to UGX: 3,582.34

USD to BIF: 2,850.0

USD to CDF: 2,700.0

🔧 Troubleshooting
Common Issues
1. MongoDB Connection Failed
text
Error: [Errno 111] Connection refused
Solution:

bash
# Start MongoDB service
sudo systemctl start mongod

# Or with Docker
docker start queenkoba-mongodb

# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"
2. Port 5000 Already in Use
text
Address already in use
Solution:

bash
# Kill process on port 5000
sudo fuser -k 5000/tcp

# Or run on different port
python queenkoba_mongodb.py --port 5001
3. Module Import Errors
text
ModuleNotFoundError: No module named 'flask'
Solution:

bash
# Reinstall requirements
pip install -r requirements.txt

# Or install manually
pip install Flask Flask-CORS pymongo Flask-PyMongo
4. JWT Token Not Working
text
Missing Authorization Header
Solution:

Ensure token is included in headers: Authorization: Bearer YOUR_TOKEN

Check if token has expired (default: 24 hours)

Login again to get new token

Debug Mode
Enable debug mode for detailed error logs:

bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python queenkoba_mongodb.py
🤝 Contributing
We welcome contributions! Please follow these steps:

Fork the repository

Create a feature branch: git checkout -b feature/amazing-feature

Commit your changes: git commit -m 'Add amazing feature'

Push to the branch: git push origin feature/amazing-feature

Open a Pull Request

Development Guidelines
Follow PEP 8 style guide

Write tests for new features

Update documentation

Use meaningful commit messages

Keep the codebase clean and organized

Project Structure
text
queen-koba-backend/
├── queenkoba_mongodb.py     # Main application
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── .gitignore              # Git ignore file
├── README.md               # This file
├── tests/                  # Test files
│   └── test_api.py
├── data/                   # Sample data
│   └── products.json
└── docs/                   # Documentation
    └── api-spec.md
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Flask - Web framework

MongoDB - Database

Flask-JWT-Extended - Authentication

bcrypt - Password hashing

📞 Support
For support, email info@queenkoba.com or create an issue in the GitHub repository.

🌟 Show Your Support
Give a ⭐️ if this project helped you!

Queen Koba Skincare API - Empowering beauty commerce in East Africa with multi-currency solutions. 💅✨












