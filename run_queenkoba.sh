#!/bin/bash
# run_queenkoba.sh - Setup and run Queen Koba API

echo "🚀 Setting up Queen Koba API..."

# Step 1: Activate venv
source venv/bin/activate

# Step 2: Install dependencies
pip install Flask Flask-CORS pymongo Flask-PyMongo python-dotenv Flask-JWT-Extended bcrypt --quiet

# Step 3: Create necessary directories
mkdir -p app/routes app/utils

# Step 4: Create .env file
cat > .env << 'ENVEOF'
FLASK_APP=run.py
FLASK_ENV=development
MONGO_URI=mongodb://localhost:27017/queenkoba
SECRET_KEY=queenkoba-secret-key-2024
JWT_SECRET_KEY=queenkoba-jwt-secret-2024
ENVEOF

# Step 5: Create run.py
cat > run.py << 'RUNEOF'
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
RUNEOF

# Step 6: Create app/__init__.py
cat > app/__init__.py << 'INITEOF'
from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

mongo = PyMongo()
cors = CORS()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    load_dotenv()
    
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/queenkoba')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    
    mongo.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app
INITEOF

# Step 7: Create main routes
cat > app/routes/main.py << 'MAINEOF'
from flask import Blueprint, jsonify, request
from app import mongo
from bson import ObjectId
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return jsonify({
        'message': 'Queen Koba Skincare API',
        'status': 'success',
        'endpoints': {
            '/': 'API info',
            '/products': 'All products',
            '/products/<id>': 'Single product',
            '/auth/register': 'Register',
            '/auth/login': 'Login',
            '/health': 'Health check'
        }
    })

@main_bp.route('/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find())
    for p in products:
        p['_id'] = str(p['_id'])
    return jsonify({
        'status': 'success',
        'count': len(products),
        'products': products
    })

@main_bp.route('/health', methods=['GET'])
def health():
    try:
        mongo.db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        })
    except:
        return jsonify({
            'status': 'degraded',
            'database': 'disconnected'
        }), 503
MAINEOF

# Step 8: Create auth routes
cat > app/routes/auth.py << 'AUTHEOF'
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import mongo
import bcrypt
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if mongo.db.users.find_one({'email': data.get('email')}):
        return jsonify({'error': 'Email exists'}), 400
    
    user = {
        '_id': str(uuid.uuid4()),
        'email': data['email'],
        'password_hash': bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode(),
        'country': data.get('country', 'Kenya'),
        'created_at': datetime.utcnow()
    }
    
    mongo.db.users.insert_one(user)
    
    token = create_access_token(identity=user['_id'])
    user.pop('password_hash')
    
    return jsonify({
        'status': 'success',
        'token': token,
        'user': user
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = mongo.db.users.find_one({'email': data.get('email')})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(data['password'].encode(), user['password_hash'].encode()):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_access_token(identity=str(user['_id']))
    user.pop('password_hash')
    user['_id'] = str(user['_id'])
    
    return jsonify({
        'status': 'success',
        'token': token,
        'user': user
    })
AUTHEOF

# Step 9: Create seed data
cat > seed_data.py << 'SEEDEOF'
from flask import Flask
from flask_pymongo import PyMongo
from datetime import datetime
import uuid
import bcrypt

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/queenkoba'
mongo = PyMongo(app)

with app.app_context():
    # Clear old data
    mongo.db.products.drop()
    mongo.db.users.drop()
    
    # Products with multi-currency prices
    products = [
        {
            'name': 'Complex Clarifier Cream',
            'description': 'Luxurious clarifying cream',
            'base_price_usd': 29.99,
            'category': 'Cream',
            'prices': [
                {'currency': 'KES', 'price': 3850, 'country': 'Kenya'},
                {'currency': 'UGX', 'price': 107400, 'country': 'Uganda'},
                {'currency': 'BIF', 'price': 85400, 'country': 'Burundi'},
                {'currency': 'CDF', 'price': 80970, 'country': 'DRC Congo'}
            ]
        },
        {
            'name': 'Complexion Clarifier Serum',
            'description': 'Vitamin C serum',
            'base_price_usd': 34.50,
            'category': 'Serum',
            'prices': [
                {'currency': 'KES', 'price': 4430, 'country': 'Kenya'},
                {'currency': 'UGX', 'price': 123500, 'country': 'Uganda'},
                {'currency': 'BIF', 'price': 98300, 'country': 'Burundi'},
                {'currency': 'CDF', 'price': 93150, 'country': 'DRC Congo'}
            ]
        }
    ]
    
    for p in products:
        p['_id'] = str(uuid.uuid4())
        p['created_at'] = datetime.utcnow()
        p['in_stock'] = True
        mongo.db.products.insert_one(p)
        print(f"Added: {p['name']}")
    
    # Admin user
    admin = {
        '_id': str(uuid.uuid4()),
        'email': 'admin@queenkoba.com',
        'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(),
        'country': 'Kenya',
        'created_at': datetime.utcnow(),
        'role': 'admin'
    }
    mongo.db.users.insert_one(admin)
    
    print(f"\n✅ Added {len(products)} products")
    print("👤 Admin: admin@queenkoba.com / admin123")
    print("\n📊 Sample prices for Cream (KES 3850, UGX 107400, etc.)")
SEEDEOF

# Step 10: Check MongoDB
echo "Checking MongoDB..."
if ! python3 -c "import pymongo; pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000).server_info()" 2>/dev/null; then
    echo "MongoDB not running. Trying to start..."
    if command -v docker &> /dev/null; then
        docker run -d -p 27017:27017 --name queenkoba-mongo mongo:latest
        sleep 3
        echo "Started MongoDB with Docker"
    else
        echo "⚠️ MongoDB not available. Using in-memory data."
    fi
fi

# Step 11: Seed data
python seed_data.py

# Step 12: Run the app
echo -e "\n🚀 Starting Queen Koba API..."
echo "👉 Open: http://localhost:5000"
echo "👉 Admin: info@queenkoba.com / info123"
echo -e "\nPress Ctrl+C to stop\n"

export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
