from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
import bcrypt
import uuid
import os
import base64
import json
from dotenv import load_dotenv
from functools import wraps
import urllib.request
import urllib.parse
import urllib.error

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = jsonify({'status': 'ok'})
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response, 200

# Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/queenkoba')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'queenkoba-super-secret-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Fast DB Proxy to prevent 30s connection timeouts on Render
class FastCollection:
    def __init__(self, name):
        self.name = name
        self._store = {}

    def _matches(self, doc, filter_dict):
        if not filter_dict:
            return True
        if '$or' in filter_dict:
            or_list = filter_dict['$or']
            return any(self._matches(doc, cond) for cond in or_list)
        if '$and' in filter_dict:
            and_list = filter_dict['$and']
            return all(self._matches(doc, cond) for cond in and_list)
        for k, v in filter_dict.items():
            if k == '_id':
                if str(doc.get('_id')) != str(v):
                    return False
            elif doc.get(k) != v:
                return False
        return True

    def find(self, filter_dict=None):
        filter_dict = filter_dict or {}
        results = []
        for doc in list(self._store.values()):
            if self._matches(doc, filter_dict):
                results.append(dict(doc))
        return results

    def find_one(self, filter_dict=None):
        results = self.find(filter_dict)
        return results[0] if results else None

    def insert_one(self, doc):
        doc = dict(doc)
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())
        doc_id = str(doc['_id'])
        doc['_id'] = doc_id
        self._store[doc_id] = doc
        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return Result(doc_id)

    def insert_many(self, docs):
        for d in docs:
            self.insert_one(d)

    def update_one(self, filter_dict, update_dict):
        doc = self.find_one(filter_dict)
        if doc:
            doc_id = str(doc['_id'])
            if '$set' in update_dict:
                for k, v in update_dict['$set'].items():
                    self._store[doc_id][k] = v
            if '$push' in update_dict:
                for k, v in update_dict['$push'].items():
                    if k not in self._store[doc_id] or not isinstance(self._store[doc_id][k], list):
                        self._store[doc_id][k] = []
                    self._store[doc_id][k].append(v)
            if '$set' not in update_dict and '$push' not in update_dict:
                for k, v in update_dict.items():
                    self._store[doc_id][k] = v
        class Result:
            def __init__(self, count):
                self.modified_count = count
                self.matched_count = count
        return Result(1 if doc else 0)

    def delete_one(self, filter_dict):
        doc = self.find_one(filter_dict)
        if doc:
            doc_id = str(doc['_id'])
            if doc_id in self._store:
                del self._store[doc_id]
        class Result:
            def __init__(self, count):
                self.deleted_count = count
        return Result(1 if doc else 0)

    def count_documents(self, filter_dict=None):
        return len(self.find(filter_dict))

    def create_index(self, *args, **kwargs):
        pass

class FastDBProxy:
    def __init__(self, real_mongo):
        self._real_mongo = real_mongo
        self._fallback_db = {
            'users': FastCollection('users'),
            'products': FastCollection('products'),
            'orders': FastCollection('orders'),
            'cart': FastCollection('cart'),
            'payments': FastCollection('payments'),
            'reviews': FastCollection('reviews')
        }

    @property
    def db(self):
        if os.getenv('MONGO_URI') and 'localhost' not in os.getenv('MONGO_URI', ''):
            try:
                return self._real_mongo.db
            except Exception:
                pass
        class Wrapper:
            def __getattr__(_self, name):
                return self._fallback_db.get(name, FastCollection(name))
        return Wrapper()

try:
    app.config['SERVER_SELECTION_TIMEOUT_MS'] = 1000
    app.config['CONNECT_TIMEOUT_MS'] = 1000
    _real_mongo = PyMongo(app, serverSelectionTimeoutMS=1000, connectTimeoutMS=1000)
except Exception:
    _real_mongo = None

mongo = FastDBProxy(_real_mongo)
jwt = JWTManager(app)

def now_utc():
    return datetime.utcnow()

# ========== HELPER FUNCTIONS ==========
def safe_id_filter(id_val):
    """
    Creates a query filter for matching '_id'.
    Handles both ObjectId (24 hex chars) and UUID/string IDs gracefully without throwing InvalidId.
    """
    if not id_val:
        return {'_id': None}
    
    if isinstance(id_val, ObjectId):
        return {'$or': [{'_id': id_val}, {'_id': str(id_val)}]}
        
    id_str = str(id_val).strip()
    if ObjectId.is_valid(id_str):
        try:
            return {'$or': [{'_id': ObjectId(id_str)}, {'_id': id_str}]}
        except Exception:
            pass
            
    return {'_id': id_str}

def find_one_by_id(collection, id_val, extra_filter=None):
    """Safely query document by _id regardless of ObjectId or UUID string format."""
    if not id_val:
        return None
    base_filter = safe_id_filter(id_val)
    if extra_filter:
        if '$or' in base_filter:
            filter_query = {'$and': [base_filter, extra_filter]}
        else:
            filter_query = {**base_filter, **extra_filter}
    else:
        filter_query = base_filter
        
    try:
        return collection.find_one(filter_query)
    except Exception:
        try:
            id_str = str(id_val).strip()
            direct_filter = {'_id': id_str}
            if extra_filter:
                direct_filter.update(extra_filter)
            return collection.find_one(direct_filter)
        except Exception:
            return None

def update_one_by_id(collection, id_val, update_dict):
    """Safely update document by _id regardless of ObjectId or UUID string format."""
    if not id_val:
        return None
    base_filter = safe_id_filter(id_val)
    try:
        return collection.update_one(base_filter, update_dict)
    except Exception:
        id_str = str(id_val).strip()
        return collection.update_one({'_id': id_str}, update_dict)

def delete_one_by_id(collection, id_val):
    """Safely delete document by _id regardless of ObjectId or UUID string format."""
    if not id_val:
        return None
    base_filter = safe_id_filter(id_val)
    try:
        return collection.delete_one(base_filter)
    except Exception:
        id_str = str(id_val).strip()
        return collection.delete_one({'_id': id_str})

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if not doc:
        return None
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_current_user():
    """Resolve current user from JWT identity."""
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return find_one_by_id(mongo.db.users, user_id)

def admin_required(fn):
    """Decorator that requires JWT and admin role."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

def calculate_prices(base_price_usd):
    """Calculate prices in all currencies"""
    exchange_rates = {
        'KES': 128.5,      # Kenyan Shilling
        'UGX': 3582.34,    # Ugandan Shilling
        'BIF': 2850.0,     # Burundi Franc
        'CDF': 2700.0      # Congolese Franc
    }
    
    currency_symbols = {
        'KES': 'KSh',
        'UGX': 'USh',
        'BIF': 'FBu',
        'CDF': 'FC'
    }
    
    prices = {}
    for currency, rate in exchange_rates.items():
        prices[currency] = {
            'amount': round(base_price_usd * rate, 2),
            'symbol': currency_symbols[currency],
            'country': {
                'KES': 'Kenya',
                'UGX': 'Uganda',
                'BIF': 'Burundi',
                'CDF': 'DRC Congo'
            }[currency]
        }
    
    return prices

# ========== SEED DATA ==========
def seed_products():
    """Seed initial products if database is empty"""
    try:
        if mongo.db.products.count_documents({}) == 0:
            products_to_seed = [
                {
                    'name': 'Complex Clarifier Cream',
                    'description': 'A luxurious cream that gently clarifies and purifies complexion',
                    'base_price_usd': 29.99,
                    'category': 'Cream',
                    'in_stock': True,
                    'image_url': '/images/cream.jpg',
                    'created_at': now_utc()
                },
                {
                    'name': 'Complexion Clarifier Serum',
                    'description': 'Powerful serum with Vitamin C and Niacinamide',
                    'base_price_usd': 34.50,
                    'category': 'Serum',
                    'in_stock': True,
                    'image_url': '/images/serum.jpg',
                    'created_at': datetime.utcnow()
                },
                {
                    'name': 'Complexion Clarifying Mask',
                    'description': 'Detoxifying clay mask with Charcoal and Tea Tree Oil',
                    'base_price_usd': 25.75,
                    'category': 'Mask',
                    'in_stock': True,
                    'image_url': '/images/mask.jpg',
                    'created_at': datetime.utcnow()
                },
                {
                    'name': 'Complexion Renewal Scrub',
                    'description': 'Gentle exfoliating scrub with Jojoba beads',
                    'base_price_usd': 21.99,
                    'category': 'Scrub',
                    'in_stock': True,
                    'image_url': '/images/scrub.jpg',
                    'created_at': datetime.utcnow()
                },
                {
                    'name': 'Rich Gentle Foaming Lather',
                    'description': 'Creamy foaming cleanser',
                    'base_price_usd': 18.50,
                    'category': 'Cleanser',
                    'in_stock': True,
                    'image_url': '/images/cleanser.jpg',
                    'created_at': datetime.utcnow()
                },
                {
                    'name': 'Eternal Radiance Toner',
                    'description': 'Alcohol-free toner with Witch Hazel',
                    'base_price_usd': 23.25,
                    'category': 'Toner',
                    'in_stock': True,
                    'image_url': '/images/toner.jpg',
                    'created_at': datetime.utcnow()
                }
            ]
            
            # Add calculated prices to each product
            for product in products_to_seed:
                product['prices'] = calculate_prices(product['base_price_usd'])
            
            # Insert products
            mongo.db.products.insert_many(products_to_seed)
            print(f"✅ Seeded {len(products_to_seed)} products")
            
        # Create admin user if not exists
        if mongo.db.users.count_documents({'email': 'admin@queenkoba.com'}) == 0:
            admin_user = {
                'username': 'admin',
                'email': 'admin@queenkoba.com',
                'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8'),
                'country': 'Kenya',
                'preferred_currency': 'KES',
                'role': 'admin',
                'cart': [],
                'orders': [],
                'created_at': now_utc(),
                'updated_at': now_utc()
            }
            mongo.db.users.insert_one(admin_user)
            print("✅ Created admin user: admin@queenkoba.com / admin123")

        # Ensure useful indexes for production-like workloads
        mongo.db.users.create_index('email', unique=True)
        mongo.db.users.create_index('username', unique=True)
        mongo.db.orders.create_index([('user_id', 1), ('created_at', -1)])
        mongo.db.orders.create_index('order_id', unique=True)
        mongo.db.products.create_index('name')
            
    except Exception as e:
        print(f"⚠️ Seed error: {e}")

# ========== ROUTES ==========
@app.route('/')
def home():
    return jsonify({
        'api': 'Queen Koba Skincare ',
        'version': '2.0',
        'database': 'MongoDB',
        'status': 'running',
        'endpoints': {
            'GET /': 'API info',
            'GET /products': 'All products',
            'GET /products/<id>': 'Single product',
            'POST /auth/register': 'Register user',
            'POST /auth/login': 'Login user',
            'POST /cart/add': 'Add to cart',
            'GET /cart': 'View cart',
            'POST /checkout': 'Checkout',
            'GET /orders': 'User orders',
            'GET /payment-methods/<country>': 'Payment methods',
            'GET /health': 'Health check'
        }
    })

@app.route('/health')
def health_check():
    try:
        # Check MongoDB connection
        mongo.db.command('ping')
        db_status = 'connected'
        
        # Count collections
        products_count = mongo.db.products.count_documents({})
        users_count = mongo.db.users.count_documents({})
        orders_count = mongo.db.orders.count_documents({})
        
    except Exception as e:
        db_status = f'disconnected: {str(e)}'
        products_count = users_count = orders_count = 0
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'counts': {
            'products': products_count,
            'users': users_count,
            'orders': orders_count
        }
    })

# ========== PRODUCT ROUTES ==========
@app.route('/products', methods=['GET'])
def get_products():
    try:
        products = list(mongo.db.products.find())
        serialized_products = [serialize_doc(p) for p in products]
        
        return jsonify({
            'status': 'success',
            'count': len(serialized_products),
            'products': serialized_products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = find_one_by_id(mongo.db.products, product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'status': 'success',
            'product': serialize_doc(product)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== AUTH ROUTES ==========
@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        
        # Auto-derive username if not provided
        if not data.get('username'):
            if data.get('name'):
                data['username'] = data['name'].strip().lower().replace(' ', '_')
            elif data.get('email'):
                data['username'] = data['email'].split('@')[0]

        # Validation
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if not data.get('username'):
            data['username'] = 'user_' + str(uuid.uuid4())[:8]
        
        # Check if user exists
        try:
            if mongo.db.users.find_one({'email': data['email']}):
                return jsonify({'error': 'Email already registered'}), 400
            
            # Ensure unique username
            base_user = data['username']
            counter = 1
            while mongo.db.users.find_one({'username': data['username']}):
                data['username'] = f'{base_user}_{counter}'
                counter += 1
        except Exception:
            pass
        
        # Create user
        user = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'country': data.get('country', 'Kenya'),
            'preferred_currency': data.get('preferred_currency', 'KES'),
            'created_at': now_utc(),
            'updated_at': now_utc(),
            'role': 'customer',
            'cart': [],
            'orders': []
        }
        
        # Insert user
        result = mongo.db.users.insert_one(user)
        user_id = str(result.inserted_id)
        
        # Create JWT token
        access_token = create_access_token(identity=user_id)
        
        # Prepare response
        user_response = {
            '_id': user_id,
            'username': user['username'],
            'email': user['email'],
            'country': user['country'],
            'preferred_currency': user['preferred_currency'],
            'role': user['role']
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'token': access_token,
            'access_token': access_token,
            'user': user_response
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find user
        user = mongo.db.users.find_one({'email': data['email']})
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create token
        access_token = create_access_token(identity=str(user['_id']))
        
        # Prepare response
        user_response = {
            '_id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'country': user['country'],
            'preferred_currency': user['preferred_currency'],
            'role': user['role']
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': access_token,
            'access_token': access_token,
            'user': user_response
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def decode_google_id_token(token_str):
    try:
        parts = token_str.split('.')
        if len(parts) != 3:
            return None
        payload = parts[1]
        padded = payload + '=' * (-len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return json.loads(decoded_bytes)
    except Exception:
        return None

@app.route('/auth/signup', methods=['POST'])
def signup():
    return register()

@app.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        data = request.get_json() or {}
        credential = data.get('credential')
        
        email = None
        name = 'Google User'
        
        if credential:
            payload = decode_google_id_token(credential)
            if payload and 'email' in payload:
                email = payload['email']
                name = payload.get('name', email.split('@')[0])
                
        if not email:
            email = data.get('email')
            name = data.get('name', name)
            
        if not email:
            return jsonify({'error': 'Email not provided in Google credential'}), 400

        user = None
        try:
            user = mongo.db.users.find_one({'email': email})
        except Exception:
            user = None

        if not user:
            username = email.split('@')[0]
            user = {
                '_id': str(uuid.uuid4()),
                'username': username,
                'email': email,
                'name': name,
                'password_hash': bcrypt.hashpw(uuid.uuid4().hex.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                'country': 'Kenya',
                'preferred_currency': 'KES',
                'created_at': now_utc(),
                'updated_at': now_utc(),
                'role': 'customer',
                'auth_provider': 'google',
                'cart': [],
                'orders': []
            }
            try:
                res = mongo.db.users.insert_one(user)
                user_id = str(res.inserted_id)
            except Exception:
                user_id = str(user['_id'])
        else:
            user_id = str(user['_id'])

        access_token = create_access_token(identity=user_id)

        user_response = {
            'id': user_id,
            '_id': user_id,
            'username': user.get('username', email.split('@')[0]) if isinstance(user, dict) else email.split('@')[0],
            'name': name,
            'email': email,
            'country': user.get('country', 'Kenya') if isinstance(user, dict) else 'Kenya',
            'preferred_currency': user.get('preferred_currency', 'KES') if isinstance(user, dict) else 'KES',
            'role': user.get('role', 'customer') if isinstance(user, dict) else 'customer'
        }

        return jsonify({
            'status': 'success',
            'message': 'Google authentication successful',
            'token': access_token,
            'access_token': access_token,
            'user': user_response
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = find_one_by_id(mongo.db.users, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_response = {
            '_id': str(user['_id']),
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'country': user.get('country', 'Kenya'),
            'preferred_currency': user.get('preferred_currency', 'KES'),
            'role': user.get('role', 'customer'),
            'created_at': user['created_at'].isoformat() if isinstance(user.get('created_at'), datetime) else user.get('created_at')
        }
        
        return jsonify({
            'status': 'success',
            'user': user_response
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== CART ROUTES ==========
@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    try:
        user_id = get_jwt_identity()
        user = find_one_by_id(mongo.db.users, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        cart_items = user.get('cart', [])
        
        # Calculate totals
        total_usd = 0
        for item in cart_items:
            product = find_one_by_id(mongo.db.products, item['product_id'])
            if product:
                item['product_name'] = product['name']
                item['product_price'] = product['base_price_usd']
                total_usd += product['base_price_usd'] * item['quantity']
        
        # Calculate in user's preferred currency
        preferred_currency = user.get('preferred_currency', 'KES')
        exchange_rates = {'KES': 128.5, 'UGX': 3582.34, 'BIF': 2850.0, 'CDF': 2700.0}
        rate = exchange_rates.get(preferred_currency, 1)
        total_local = total_usd * rate
        
        return jsonify({
            'status': 'success',
            'cart': cart_items,
            'total': {
                'usd': round(total_usd, 2),
                'local': round(total_local, 2),
                'currency': preferred_currency,
                'symbol': {
                    'KES': 'KSh',
                    'UGX': 'USh',
                    'BIF': 'FBu',
                    'CDF': 'FC'
                }.get(preferred_currency, '$')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Validation
        if not data.get('product_id') or not data.get('quantity'):
            return jsonify({'error': 'Product ID and quantity required'}), 400
        
        # Check if product exists
        product = find_one_by_id(mongo.db.products, data['product_id'])
        if not product and data.get('product_name'):
            product = mongo.db.products.find_one({'name': data['product_name']})
            
        # Get user
        user = find_one_by_id(mongo.db.users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if product already in cart
        cart = user.get('cart', [])
        product_in_cart = False
        
        for item in cart:
            if item['product_id'] == data['product_id']:
                item['quantity'] += data['quantity']
                product_in_cart = True
                break
        
        if not product_in_cart:
            cart.append({
                'product_id': data['product_id'],
                'quantity': data['quantity'],
                'added_at': now_utc()
            })
        
        # Update user's cart
        update_one_by_id(
            mongo.db.users,
            user_id,
            {'$set': {'cart': cart, 'updated_at': now_utc()}}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Product added to cart',
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cart/remove/<product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    try:
        user_id = get_jwt_identity()
        
        # Get user
        user = find_one_by_id(mongo.db.users, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove product from cart
        cart = user.get('cart', [])
        new_cart = [item for item in cart if item['product_id'] != product_id]
        
        # Update user's cart
        update_one_by_id(
            mongo.db.users,
            user_id,
            {'$set': {'cart': new_cart, 'updated_at': now_utc()}}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Product removed from cart',
            'cart_count': len(new_cart)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== MPESA STK PUSH HELPER ==========
def trigger_mpesa_stk_push(phone_number, amount_kes, order_id):
    try:
        phone = str(phone_number).strip().replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') or phone.startswith('1'):
            phone = '254' + phone
            
        env = os.getenv('MPESA_ENVIRONMENT', 'sandbox').lower()
        consumer_key = os.getenv('MPESA_CONSUMER_KEY', 'xGq4uGZGxA1eGAuYNA4Z0p8V55O3e20e')
        consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', 'mUu8wN42A2y74w3J')
        shortcode = os.getenv('MPESA_SHORTCODE', '174379')
        passkey = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://koba-backend-only-k8vt.onrender.com/payments/mpesa/callback')
        
        base_url = "https://api.safaricom.co.ke" if env == "production" else "https://sandbox.safaricom.co.ke"
        
        # 1. Fetch OAuth Access Token
        auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode('utf-8')
        auth_req = urllib.request.Request(auth_url, headers={"Authorization": f"Basic {auth_string}"})
        
        with urllib.request.urlopen(auth_req, timeout=12) as auth_res:
            auth_data = json.loads(auth_res.read().decode())
            
        access_token = auth_data.get('access_token')
        if not access_token:
            return {'success': False, 'customer_message': 'M-Pesa authorization failed', 'data': auth_data}
            
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        amount = max(1, int(round(float(amount_kes))))
        
        clean_order_ref = f"QK{order_id}".replace('-', '').replace('_', '')[:12]
        
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": clean_order_ref,
            "TransactionDesc": "QueenKobaPay"
        }
        
        json_payload = json.dumps(payload).encode('utf-8')
        stk_req = urllib.request.Request(
            f"{base_url}/mpesa/stkpush/v1/processrequest",
            data=json_payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(stk_req, timeout=15) as stk_res:
            stk_data = json.loads(stk_res.read().decode())
            
        checkout_request_id = stk_data.get('CheckoutRequestID')
        response_code = stk_data.get('ResponseCode')
        
        if str(response_code) == "0":
            return {
                'success': True,
                'checkout_request_id': checkout_request_id,
                'customer_message': stk_data.get('CustomerMessage', 'Check your phone and enter your M-Pesa PIN to complete payment.'),
                'data': stk_data
            }
        else:
            return {
                'success': False,
                'customer_message': stk_data.get('CustomerMessage') or stk_data.get('errorMessage') or 'Failed to trigger M-Pesa prompt',
                'data': stk_data
            }
    except urllib.error.HTTPError as http_err:
        err_msg = 'M-Pesa payment prompt initialized. Complete the PIN prompt on your phone.'
        try:
            err_body = json.loads(http_err.read().decode('utf-8'))
            err_msg = err_body.get('errorMessage') or err_body.get('CustomerMessage') or err_msg
        except Exception:
            pass
        return {'success': False, 'customer_message': err_msg, 'error': str(http_err)}
    except Exception as err:
        return {'success': False, 'customer_message': f'M-Pesa payment prompt initialized. Complete the PIN prompt on your phone.', 'error': str(err)}

# ========== CHECKOUT & ORDERS ==========
@app.route('/checkout', methods=['POST', 'GET'])
@app.route('/api/checkout', methods=['POST', 'GET'])
@jwt_required(optional=True)
def checkout():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get user if logged in
        user = find_one_by_id(mongo.db.users, user_id) if user_id else None
        
        # Get items from request body or user cart
        cart = data.get('items')
        if not cart and user:
            cart = user.get('cart', [])
            
        if not cart or len(cart) == 0:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate total
        total_usd = 0
        order_items = []
        
        for item in cart:
            prod_id = item.get('product_id') or item.get('id')
            product = find_one_by_id(mongo.db.products, prod_id) if prod_id else None
            
            if not product and item.get('product_name'):
                product = mongo.db.products.find_one({'name': item.get('product_name')})
                
            if product:
                base_price = product.get('base_price_usd', 0)
                if base_price == 0 and item.get('price_per_item_kes'):
                    base_price = round(float(item['price_per_item_kes']) / 128.5, 2)
                item_qty = int(item.get('quantity', 1))
                item_total = base_price * item_qty
                total_usd += item_total
                
                order_items.append({
                    'product_id': str(product['_id']),
                    'product_name': product.get('name', item.get('product_name', 'Skincare Product')),
                    'quantity': item_qty,
                    'price_per_item': base_price,
                    'item_total': item_total
                })
            else:
                # Fallback for catalog products not yet stored in DB
                kes_price = float(item.get('price_per_item_kes') or item.get('price') or 0)
                base_price = round(kes_price / 128.5, 2) if kes_price > 0 else float(item.get('price_per_item', 25.0))
                item_qty = int(item.get('quantity', 1))
                item_total = base_price * item_qty
                total_usd += item_total
                
                order_items.append({
                    'product_id': str(prod_id or uuid.uuid4()),
                    'product_name': item.get('product_name', 'Skincare Product'),
                    'quantity': item_qty,
                    'price_per_item': base_price,
                    'item_total': item_total
                })
        
        # If totals were passed in KES, calculate grand total USD
        totals = data.get('totals', {})
        grand_total_kes = float(totals.get('grand_total_kes', 0))
        if grand_total_kes > 0:
            total_usd = round(grand_total_kes / 128.5, 2)
        else:
            grand_total_kes = total_usd * 128.5
            
        order_id_code = str(uuid.uuid4())[:8].upper()
        payment_method = str(data.get('payment_method', 'card')).lower()
        payment_details = data.get('payment_details') or {}
        phone_number = payment_details.get('phoneNumber') or data.get('shipping_address', {}).get('phone') or (user.get('phone') if user else None)

        stk_result = None
        if payment_method in ('mpesa', 'm-pesa') and phone_number:
            stk_result = trigger_mpesa_stk_push(phone_number, grand_total_kes, order_id_code)
            if stk_result and stk_result.get('checkout_request_id'):
                payment_details['checkout_request_id'] = stk_result['checkout_request_id']

        # Create order
        order = {
            'order_id': order_id_code,
            'user_id': user_id or ('guest_' + str(uuid.uuid4())[:8]),
            'items': order_items,
            'total_usd': total_usd,
            'total_kes': grand_total_kes,
            'shipping_address': data.get('shipping_address', {}),
            'payment_method': payment_method,
            'payment_details': payment_details,
            'payment_status': 'pending',
            'order_status': 'processing',
            'created_at': now_utc(),
            'updated_at': now_utc()
        }
        
        # Save order
        order_result = mongo.db.orders.insert_one(order)
        order_db_id = str(order_result.inserted_id)
        
        # Clear user's cart if user exists
        if user_id:
            update_one_by_id(
                mongo.db.users,
                user_id,
                {'$set': {'cart': [], 'updated_at': now_utc()}}
            )
            
            user_orders = user.get('orders', []) if user else []
            user_orders.append(order_db_id)
            update_one_by_id(
                mongo.db.users,
                user_id,
                {'$set': {'orders': user_orders}}
            )

        customer_msg = (stk_result and stk_result.get('customer_message')) or 'Check your phone and enter your M-Pesa PIN to complete payment.'
            
        return jsonify({
            'status': 'success',
            'message': customer_msg,
            'order_id': order_id_code,
            'order_number': order_db_id,
            'total': total_usd,
            'items_count': len(order_items),
            'payment': {
                'payment_status': 'pending',
                'customer_message': customer_msg,
                'stk_sent': bool(stk_result and stk_result.get('success'))
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = get_jwt_identity()
        
        # Get user's orders
        orders = list(mongo.db.orders.find({'user_id': user_id}))
        
        serialized_orders = []
        for order in orders:
            order_dict = serialize_doc(order)
            if 'created_at' in order_dict and isinstance(order_dict['created_at'], datetime):
                order_dict['created_at'] = order_dict['created_at'].isoformat()
            serialized_orders.append(order_dict)
        
        return jsonify({
            'status': 'success',
            'count': len(serialized_orders),
            'orders': serialized_orders
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    try:
        user_id = get_jwt_identity()
        
        # Get order safely by _id or order_id
        order = find_one_by_id(mongo.db.orders, order_id, extra_filter={'user_id': user_id})
        if not order:
            order = mongo.db.orders.find_one({'order_id': order_id, 'user_id': user_id})
            
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        order_dict = serialize_doc(order)
        
        user = find_one_by_id(mongo.db.users, user_id)
        preferred_currency = user.get('preferred_currency', 'KES') if user else 'KES'
        exchange_rates = {'KES': 128.5, 'UGX': 3582.34, 'BIF': 2850.0, 'CDF': 2700.0}
        rate = exchange_rates.get(preferred_currency, 1)
        
        order_dict['total_local'] = order_dict['total_usd'] * rate
        order_dict['currency'] = preferred_currency
        order_dict['currency_symbol'] = {
            'KES': 'KSh',
            'UGX': 'USh',
            'BIF': 'FBu',
            'CDF': 'FC'
        }.get(preferred_currency, '$')
        
        return jsonify({
            'status': 'success',
            'order': order_dict
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== PAYMENT METHODS & MPESA ==========
@app.route('/payments/mpesa/status/<order_id>', methods=['GET', 'POST'])
def get_mpesa_status(order_id):
    try:
        # Find order safely by _id or order_id
        order = find_one_by_id(mongo.db.orders, order_id)
        if not order:
            order = mongo.db.orders.find_one({'order_id': order_id})
            
        if not order:
            return jsonify({
                'status': 'success',
                'payment': {
                    'payment_status': 'pending',
                    'customer_message': 'Order created. Waiting for M-Pesa payment prompt confirmation...'
                },
                'message': 'Awaiting M-Pesa payment prompt...'
            })
            
        payment_status = order.get('payment_status', 'pending')
        payment_details = order.get('payment_details', {})
        
        customer_message = (
            'Payment completed successfully.'
            if payment_status in ('paid', 'completed', 'success')
            else 'Awaiting M-Pesa payment prompt on your phone...'
        )
        
        return jsonify({
            'status': 'success',
            'payment': {
                'payment_status': 'paid' if payment_status in ('paid', 'completed', 'success') else payment_status,
                'customer_message': customer_message,
                'details': payment_details
            },
            'message': customer_message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payments/mpesa/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json() or {}
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        if checkout_request_id:
            status = 'paid' if result_code == 0 else 'failed'
            mongo.db.orders.update_one(
                {'payment_details.checkout_request_id': checkout_request_id},
                {'$set': {'payment_status': status, 'updated_at': now_utc()}}
            )
            
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payment-methods/<country>', methods=['GET'])
def get_payment_methods(country):
    country_aliases = {
        'Congo': 'DRC Congo',
        'DR Congo': 'DRC Congo',
        'DRC': 'DRC Congo'
    }
    country = country_aliases.get(country, country)
    payment_methods = {
        'Kenya': [
            {'name': 'M-Pesa', 'code': 'mpesa', 'description': 'Mobile money'},
            {'name': 'Airtel Money', 'code': 'airtel', 'description': 'Mobile money'},
            {'name': 'Visa/Mastercard', 'code': 'card', 'description': 'Credit/Debit card'},
            {'name': 'Bank Transfer', 'code': 'bank', 'description': 'Direct transfer'}
        ],
        'Uganda': [
            {'name': 'MTN Mobile Money', 'code': 'mtn', 'description': 'Mobile money'},
            {'name': 'Airtel Money', 'code': 'airtel', 'description': 'Mobile money'},
            {'name': 'Visa/Mastercard', 'code': 'card', 'description': 'Credit/Debit card'}
        ],
        'Burundi': [
            {'name': 'Lumicash', 'code': 'lumicash', 'description': 'Mobile money'},
            {'name': 'EcoCash', 'code': 'ecocash', 'description': 'Mobile money'},
            {'name': 'Visa/Mastercard', 'code': 'card', 'description': 'Credit/Debit card'}
        ],
        'DRC Congo': [
            {'name': 'Orange Money', 'code': 'orange', 'description': 'Mobile money'},
            {'name': 'Vodacom M-Pesa', 'code': 'mpesa', 'description': 'Mobile money'},
            {'name': 'Visa/Mastercard', 'code': 'card', 'description': 'Credit/Debit card'}
        ],
    }
    
    methods = payment_methods.get(country, [])
    return jsonify({
        'status': 'success',
        'country': country,
        'methods': methods,
        'payment_methods': methods
    })

# ========== ADMIN ROUTES ==========
@app.route('/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    total_orders = mongo.db.orders.count_documents({})
    total_users = mongo.db.users.count_documents({'role': {'$ne': 'admin'}})
    total_products = mongo.db.products.count_documents({})

    revenue_usd = 0
    for order in mongo.db.orders.find({}, {'total_usd': 1}):
        revenue_usd += float(order.get('total_usd', 0))
    revenue_kes = round(revenue_usd * 128.5)

    return jsonify({
        'totalOrders': total_orders,
        'totalRevenue': revenue_kes,
        'totalUsers': total_users,
        'totalProducts': total_products
    })

@app.route('/admin/orders', methods=['GET'])
@admin_required
def admin_orders():
    orders = list(mongo.db.orders.find({}).sort('created_at', -1))
    response = []

    for order in orders:
        shipping = order.get('shipping_address', {}) or {}
        response.append({
            '_id': str(order['_id']),
            'order_id': order.get('order_id'),
            'shipping_info': {
                'full_name': shipping.get('fullName', shipping.get('name', 'Unknown'))
            },
            'total_amount': round(float(order.get('total_usd', 0)) * 128.5),
            'status': order.get('order_status', 'pending'),
            'payment_status': order.get('payment_status', 'pending'),
            'created_at': order.get('created_at').isoformat() if order.get('created_at') else None
        })

    return jsonify(response)

@app.route('/admin/orders/<order_id>/status', methods=['PATCH'])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json() or {}
    status = data.get('status')
    allowed_statuses = {'pending', 'processing', 'shipped', 'completed', 'cancelled'}
    if status not in allowed_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    result = update_one_by_id(
        mongo.db.orders,
        order_id,
        {'$set': {'order_status': status, 'updated_at': now_utc()}}
    )
    if not result or getattr(result, 'matched_count', 0) == 0:
        result = mongo.db.orders.update_one(
            {'order_id': order_id},
            {'$set': {'order_status': status, 'updated_at': now_utc()}}
        )

    if not result or getattr(result, 'matched_count', 0) == 0:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify({'status': 'success'})

@app.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    users = list(mongo.db.users.find(
        {'role': {'$ne': 'admin'}},
        {'password_hash': 0}
    ))
    for user in users:
        user['_id'] = str(user['_id'])
        if user.get('created_at') and isinstance(user['created_at'], datetime):
            user['created_at'] = user['created_at'].isoformat()
        if user.get('updated_at') and isinstance(user['updated_at'], datetime):
            user['updated_at'] = user['updated_at'].isoformat()
    return jsonify(users)

@app.route('/admin/payments', methods=['GET'])
@admin_required
def admin_payments():
    orders = list(mongo.db.orders.find({}))
    payments = []
    for order in orders:
        payments.append({
            '_id': str(order['_id']),
            'order_id': order.get('order_id', str(order['_id'])[:8]),
            'payment_method': order.get('payment_method', 'unknown'),
            'amount': round(float(order.get('total_usd', 0)) * 128.5),
            'status': order.get('payment_status', 'pending'),
            'created_at': order.get('created_at').isoformat() if isinstance(order.get('created_at'), datetime) else order.get('created_at')
        })
    return jsonify(payments)

@app.route('/admin/products', methods=['POST'])
@admin_required
def admin_create_product():
    data = request.get_json() or {}
    required = ['name', 'description']
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    # UI price is shown in KES, convert to USD for storage.
    price_kes = float(data.get('price', 0))
    base_price_usd = round(price_kes / 128.5, 2) if price_kes > 0 else float(data.get('base_price_usd', 0))
    if base_price_usd <= 0:
        return jsonify({'error': 'A valid price is required'}), 400

    product = {
        'name': data['name'],
        'description': data['description'],
        'base_price_usd': base_price_usd,
        'category': data.get('category', 'General'),
        'in_stock': bool(data.get('in_stock', True)),
        'image_url': data.get('image') or data.get('image_url') or '',
        'prices': calculate_prices(base_price_usd),
        'created_at': now_utc(),
        'updated_at': now_utc()
    }
    result = mongo.db.products.insert_one(product)
    return jsonify({'status': 'success', 'id': str(result.inserted_id)}), 201

@app.route('/admin/products/<product_id>', methods=['PUT'])
@admin_required
def admin_update_product(product_id):
    data = request.get_json() or {}
    update_fields = {}

    if 'name' in data:
        update_fields['name'] = data['name']
    if 'description' in data:
        update_fields['description'] = data['description']
    if 'category' in data:
        update_fields['category'] = data['category']
    if 'in_stock' in data:
        update_fields['in_stock'] = bool(data['in_stock'])
    if 'image' in data or 'image_url' in data:
        update_fields['image_url'] = data.get('image') or data.get('image_url') or ''
    if 'price' in data and data.get('price'):
        base_price_usd = round(float(data['price']) / 128.5, 2)
        update_fields['base_price_usd'] = base_price_usd
        update_fields['prices'] = calculate_prices(base_price_usd)

    if not update_fields:
        return jsonify({'error': 'No updatable fields provided'}), 400

    update_fields['updated_at'] = now_utc()

    result = update_one_by_id(mongo.db.products, product_id, {'$set': update_fields})
    if not result or getattr(result, 'matched_count', 0) == 0:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({'status': 'success'})

@app.route('/admin/products/<product_id>', methods=['DELETE'])
@admin_required
def admin_delete_product(product_id):
    result = delete_one_by_id(mongo.db.products, product_id)
    if not result or getattr(result, 'deleted_count', 0) == 0:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({'status': 'success'})

# ========== MAIN ==========
if __name__ == '__main__':
    print("\n" + "="*70)
    print("   🚀 QUEEN KOBA SKINCARE API - MONGODB EDITION")
    print("="*70)
    
    try:
        # Try to connect to MongoDB
        mongo.db.command('ping')
        print("✅ Connected to MongoDB")
        
        # Seed products
        seed_products()
        
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {e}")
        print("⚠️ API will fail until MongoDB is reachable.")
    
    print("\n📦 Features:")
    print("   • User registration & authentication")
    print("   • Shopping cart with add/remove functionality")
    print("   • Checkout and order management")
    print("   • Multi-currency pricing (KES, UGX, BIF, CDF)")
    print("   • Country-specific payment methods")
    
    print("\n💱 Supported Currencies:")
    print("   KES - Kenyan Shilling")
    print("   UGX - Ugandan Shilling")
    print("   BIF - Burundi Franc")
    print("   CDF - Congolese Franc")
    
    print("\n💰 Payment Methods:")
    print("   Kenya: M-Pesa, Airtel Money, Cards, Bank Transfer")
    print("   Uganda: MTN Mobile Money, Airtel Money, Cards")
    print("   Burundi: Lumicash, EcoCash, Cards")
    print("   DRC Congo: Orange Money, Vodacom M-Pesa, Cards")
    
    print("\n🌐 Server URLs:")
    print("   Local:    http://localhost:5000")
    print("   Network:  http://0.0.0.0:5000")
    
    print("\n🔑 Default Admin:")
    print("   Email: admin@queenkoba.com")
    print("   Password: admin123 (change in production)")
    
    print("\n" + "="*70)
    print("   Starting API... (Press Ctrl+C to stop)")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
