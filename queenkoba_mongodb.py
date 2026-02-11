from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta
import bcrypt
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/queenkoba')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'queenkoba-super-secret-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
mongo = PyMongo(app)
jwt = JWTManager(app)

# ========== HELPER FUNCTIONS ==========
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if not doc:
        return None
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

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
                    'created_at': datetime.utcnow()
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
                'email': 'info@queenkoba.com',
                'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8'),
                'country': 'Kenya',
                'preferred_currency': 'KES',
                'role': 'admin',
                'cart': [],
                'orders': [],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            mongo.db.users.insert_one(admin_user)
            print("✅ Created admin user: info@queenkoba.com / N/A")
            
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
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'status': 'success',
            'product': serialize_doc(product)
        })
    except:
        return jsonify({'error': 'Invalid product ID'}), 400

# ========== AUTH ROUTES ==========
@app.route('/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not data.get('password') or not data.get('name') or not data.get('phone'):
            return jsonify({'message': 'Name, email, phone and password required'}), 400
        
        # Check if user exists
        if mongo.db.users.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already registered'}), 400
        
        # Create user
        user = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'password_hash': bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'role': 'customer',
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.users.insert_one(user)
        user_id = str(result.inserted_id)
        
        # Create JWT token
        token = create_access_token(identity=user_id)
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email'],
                'phone': user['phone']
            }
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def customer_login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password required'}), 400
        
        # Find user
        user = mongo.db.users.find_one({'email': data['email'], 'role': 'customer'})
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Check password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Create token
        token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user.get('name', user.get('username', '')),
                'email': user['email'],
                'phone': user.get('phone', '')
            }
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/auth/google', methods=['GET'])
def google_login():
    # Placeholder for Google OAuth - requires Google OAuth setup
    return jsonify({'message': 'Google OAuth not configured yet'}), 501

@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user exists
        if mongo.db.users.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already registered'}), 400
        
        if mongo.db.users.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create user
        user = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'country': data.get('country', 'Kenya'),
            'preferred_currency': data.get('preferred_currency', 'KES'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
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
            'access_token': access_token,
            'user': user_response
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
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
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_response = {
            '_id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'country': user['country'],
            'preferred_currency': user['preferred_currency'],
            'role': user['role'],
            'created_at': user['created_at'].isoformat() if 'created_at' in user else None
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
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        cart_items = user.get('cart', [])
        
        # Calculate totals
        total_usd = 0
        for item in cart_items:
            product = mongo.db.products.find_one({'_id': ObjectId(item['product_id'])})
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
        data = request.get_json()
        
        # Validation
        if not data.get('product_id') or not data.get('quantity'):
            return jsonify({'error': 'Product ID and quantity required'}), 400
        
        # Check if product exists
        product = mongo.db.products.find_one({'_id': ObjectId(data['product_id'])})
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get user
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
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
                'added_at': datetime.utcnow()
            })
        
        # Update user's cart
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'cart': cart, 'updated_at': datetime.utcnow()}}
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
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove product from cart
        cart = user.get('cart', [])
        new_cart = [item for item in cart if item['product_id'] != product_id]
        
        # Update user's cart
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'cart': new_cart, 'updated_at': datetime.utcnow()}}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Product removed from cart',
            'cart_count': len(new_cart)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== CHECKOUT & ORDERS ==========
@app.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        cart = user.get('cart', [])
        if len(cart) == 0:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate total
        total_usd = 0
        order_items = []
        
        for item in cart:
            product = mongo.db.products.find_one({'_id': ObjectId(item['product_id'])})
            if product:
                item_total = product['base_price_usd'] * item['quantity']
                total_usd += item_total
                
                order_items.append({
                    'product_id': str(product['_id']),
                    'product_name': product['name'],
                    'quantity': item['quantity'],
                    'price_per_item': product['base_price_usd'],
                    'item_total': item_total
                })
        
        # Create order
        order = {
            'order_id': str(uuid.uuid4())[:8].upper(),
            'user_id': user_id,
            'items': order_items,
            'total_usd': total_usd,
            'shipping_address': data.get('shipping_address', {}),
            'payment_method': data.get('payment_method', 'card'),
            'payment_status': 'pending',
            'order_status': 'processing',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Save order
        order_result = mongo.db.orders.insert_one(order)
        order_id = str(order_result.inserted_id)
        
        # Clear user's cart
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'cart': [], 'updated_at': datetime.utcnow()}}
        )
        
        # Add order to user's orders
        user_orders = user.get('orders', [])
        user_orders.append(order_id)
        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'orders': user_orders}}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Order created successfully',
            'order_id': order['order_id'],
            'order_number': order_id,
            'total': total_usd,
            'items_count': len(order_items)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = get_jwt_identity()
        
        # Get user's orders
        orders = list(mongo.db.orders.find({'user_id': user_id}).sort('created_at', -1))
        
        serialized_orders = []
        for order in orders:
            order_dict = serialize_doc(order)
            # Convert datetime to string
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
        
        # Get order
        order = mongo.db.orders.find_one({
            '_id': ObjectId(order_id),
            'user_id': user_id
        })
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        order_dict = serialize_doc(order)
        
        # Calculate local currency total
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        preferred_currency = user.get('preferred_currency', 'KES')
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

# ========== ADMIN ROUTES ==========
@app.route('/admin/auth/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find admin user
        user = mongo.db.users.find_one({'email': data['email']})
        if not user or user.get('role') not in ['admin', 'super_admin']:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if suspended
        if user.get('status') == 'suspended':
            return jsonify({'error': 'Account suspended'}), 403
        
        # Check password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            'token': access_token,
            'user': {
                '_id': str(user['_id']),
                'email': user['email'],
                'full_name': user.get('username', 'Admin'),
                'role': user.get('role', 'admin'),
                'permissions': user.get('permissions', ['*'])
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/dashboard/kpis', methods=['GET'])
@jwt_required()
def get_dashboard_kpis():
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Total Revenue
        revenue_pipeline = [
            {'$match': {'created_at': {'$gte': thirty_days_ago}, 'payment_status': 'paid'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total_usd'}}}
        ]
        revenue_result = list(mongo.db.orders.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]['total'] if revenue_result else 0
        
        # Total Orders
        total_orders = mongo.db.orders.count_documents({'created_at': {'$gte': thirty_days_ago}})
        
        # Total Customers
        total_customers = mongo.db.users.count_documents({'role': 'customer'})
        
        # Conversion Rate
        conversion_rate = 3.2
        
        # Low Stock Items
        low_stock = mongo.db.products.count_documents({'in_stock': False})
        
        # Expiring Soon
        expiring_soon = 0
        
        return jsonify({
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'conversion_rate': conversion_rate,
            'refund_rate': 0.5,
            'low_stock_items': low_stock,
            'expiring_soon': expiring_soon
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/products', methods=['GET'])
@jwt_required()
def admin_get_products():
    try:
        products = list(mongo.db.products.find())
        return jsonify({
            'products': [serialize_doc(p) for p in products],
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/products', methods=['POST'])
@jwt_required()
def admin_create_product():
    try:
        data = request.get_json()
        
        new_product = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'category': data.get('category', 'Other'),
            'base_price_usd': data.get('base_price_usd', 0),
            'prices': data.get('prices', {}),
            'in_stock': data.get('in_stock', True),
            'image_url': data.get('image_url', '/images/product.jpg'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.products.insert_one(new_product)
        new_product['_id'] = str(result.inserted_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Product created successfully',
            'product': serialize_doc(new_product)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/products/<product_id>', methods=['PUT'])
@jwt_required()
def admin_update_product(product_id):
    try:
        data = request.get_json()
        
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'category' in data:
            update_data['category'] = data['category']
        if 'in_stock' in data:
            update_data['in_stock'] = data['in_stock']
        if 'prices' in data:
            update_data['prices'] = data['prices']
            # Also update base_price_usd if KES price is provided
            if isinstance(data['prices'], dict) and 'KES' in data['prices']:
                kes_amount = data['prices']['KES'].get('amount', 0)
                update_data['base_price_usd'] = round(kes_amount / 128.5, 2)
        
        result = mongo.db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Product not found'}), 404
        
        updated_product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
        
        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully',
            'product': serialize_doc(updated_product)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/products/<product_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_product(product_id):
    try:
        result = mongo.db.products.delete_one({'_id': ObjectId(product_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Product deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/orders', methods=['GET'])
@jwt_required()
def admin_get_orders():
    try:
        orders = list(mongo.db.orders.find().sort('created_at', -1).limit(50))
        return jsonify({
            'orders': [serialize_doc(o) for o in orders],
            'total': len(orders)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/orders/<order_id>/status', methods=['PUT'])
@jwt_required()
def admin_update_order_status(order_id):
    try:
        data = request.get_json()
        status = data.get('status')
        note = data.get('note', '')
        
        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {
                'order_status': status,
                'updated_at': datetime.utcnow(),
                'status_note': note
            }}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/customers', methods=['GET'])
@jwt_required()
def admin_get_customers():
    try:
        customers = list(mongo.db.users.find({'role': 'customer'}).limit(50))
        return jsonify({
            'customers': [serialize_doc(c) for c in customers],
            'total': len(customers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== PROMOTIONS ==========
@app.route('/promotions/active', methods=['GET'])
def get_active_promotions():
    try:
        promotions = list(mongo.db.promotions.find({'status': 'active'}))
        return jsonify({
            'promotions': [serialize_doc(p) for p in promotions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/promotions', methods=['GET'])
@jwt_required()
def admin_get_promotions():
    try:
        promotions = list(mongo.db.promotions.find())
        return jsonify({
            'promotions': [serialize_doc(p) for p in promotions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/promotions', methods=['POST'])
@jwt_required()
def admin_create_promotion():
    try:
        data = request.get_json()
        promo = {
            'code': data.get('code', '').upper(),
            'discount': data.get('discount', 0),
            'type': data.get('type', 'percentage'),
            'status': 'active',
            'uses': 0,
            'limit': data.get('limit'),
            'expires': data.get('expires'),
            'created_at': datetime.utcnow()
        }
        result = mongo.db.promotions.insert_one(promo)
        promo['_id'] = str(result.inserted_id)
        return jsonify({
            'status': 'success',
            'promotion': serialize_doc(promo)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/promotions/<promo_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_promotion(promo_id):
    try:
        mongo.db.promotions.delete_one({'_id': ObjectId(promo_id)})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/promotions/<promo_id>/status', methods=['PUT'])
@jwt_required()
def admin_update_promotion_status(promo_id):
    try:
        data = request.get_json()
        mongo.db.promotions.update_one(
            {'_id': ObjectId(promo_id)},
            {'$set': {'status': data.get('status')}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== REVIEWS ==========
@app.route('/admin/reviews', methods=['GET'])
@jwt_required()
def admin_get_reviews():
    try:
        reviews = list(mongo.db.reviews.find().sort('created_at', -1))
        return jsonify({
            'reviews': [serialize_doc(r) for r in reviews]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reviews/<review_id>/approve', methods=['PUT'])
@jwt_required()
def admin_approve_review(review_id):
    try:
        mongo.db.reviews.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': {'status': 'approved'}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reviews/<review_id>/reject', methods=['PUT'])
@jwt_required()
def admin_reject_review(review_id):
    try:
        mongo.db.reviews.update_one(
            {'_id': ObjectId(review_id)},
            {'$set': {'status': 'rejected'}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/reviews/<review_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_review(review_id):
    try:
        mongo.db.reviews.delete_one({'_id': ObjectId(review_id)})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews/approved', methods=['GET'])
def get_approved_reviews():
    try:
        reviews = list(mongo.db.reviews.find({'status': 'approved'}).sort('created_at', -1).limit(50))
        return jsonify({
            'reviews': [serialize_doc(r) for r in reviews]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/products/<product_id>/reviews', methods=['POST'])
def create_review(product_id):
    try:
        data = request.get_json()
        review = {
            'product_id': product_id,
            'product_name': data.get('product_name'),
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email'),
            'rating': data.get('rating', 5),
            'comment': data.get('comment'),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        result = mongo.db.reviews.insert_one(review)
        return jsonify({
            'status': 'success',
            'message': 'Review submitted for moderation',
            'review_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== PAYMENTS ==========
@app.route('/admin/payments', methods=['GET'])
@jwt_required()
def admin_get_payments():
    try:
        # Get payments from orders
        orders = list(mongo.db.orders.find().sort('created_at', -1))
        payments = []
        
        for order in orders:
            payment = {
                '_id': str(order['_id']),
                'order_id': order.get('order_id'),
                'customer_email': order.get('customer_email', 'N/A'),
                'customer_name': order.get('shipping_address', {}).get('name', 'N/A'),
                'amount': order.get('total_usd', 0),
                'payment_method': order.get('payment_method', 'card'),
                'payment_status': order.get('payment_status', 'pending'),
                'created_at': order.get('created_at')
            }
            payments.append(payment)
        
        return jsonify({
            'payments': payments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== SHIPPING ZONES ==========
@app.route('/admin/shipping-zones', methods=['GET'])
@jwt_required()
def admin_get_shipping_zones():
    try:
        zones = list(mongo.db.shipping_zones.find())
        return jsonify({
            'zones': [serialize_doc(z) for z in zones]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/shipping-zones', methods=['POST'])
@jwt_required()
def admin_create_shipping_zone():
    try:
        data = request.get_json()
        zone = {
            'name': data.get('name'),
            'rate': data.get('rate'),
            'currency': data.get('currency', 'KES'),
            'delivery_days': data.get('delivery_days'),
            'active': True,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.shipping_zones.insert_one(zone)
        zone['_id'] = str(result.inserted_id)
        return jsonify({
            'status': 'success',
            'zone': serialize_doc(zone)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/shipping-zones/<zone_id>', methods=['PUT'])
@jwt_required()
def admin_update_shipping_zone(zone_id):
    try:
        data = request.get_json()
        mongo.db.shipping_zones.update_one(
            {'_id': ObjectId(zone_id)},
            {'$set': {
                'name': data.get('name'),
                'rate': data.get('rate'),
                'delivery_days': data.get('delivery_days')
            }}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/shipping-zones/<zone_id>/status', methods=['PUT'])
@jwt_required()
def admin_toggle_shipping_zone(zone_id):
    try:
        data = request.get_json()
        mongo.db.shipping_zones.update_one(
            {'_id': ObjectId(zone_id)},
            {'$set': {'active': data.get('active')}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/shipping-zones/<zone_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_shipping_zone(zone_id):
    try:
        mongo.db.shipping_zones.delete_one({'_id': ObjectId(zone_id)})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/shipping-zones/active', methods=['GET'])
def get_active_shipping_zones():
    try:
        zones = list(mongo.db.shipping_zones.find({'active': True}))
        return jsonify({
            'zones': [serialize_doc(z) for z in zones]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== CONTENT MANAGEMENT ==========
@app.route('/admin/content', methods=['GET'])
@jwt_required()
def admin_get_content():
    try:
        content = mongo.db.site_content.find_one({'_id': 'main'})
        if not content:
            # Create default content
            content = {
                '_id': 'main',
                'hero_title': 'Queen Koba Skincare',
                'hero_subtitle': 'Luxurious skincare for melanin-rich skin',
                'about_title': 'Our Story',
                'about_description': 'Queen Koba is dedicated to creating premium skincare products for melanin-rich skin.',
                'contact_email': 'info@queenkoba.com',
                'contact_phone': '0119 559 180',
                'contact_whatsapp': '0119 559 180',
                'instagram_handle': '@queenkoba',
                'footer_text': '© 2024 Queen Koba. All rights reserved.',
            }
            mongo.db.site_content.insert_one(content)
        return jsonify({'content': serialize_doc(content)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/content', methods=['PUT'])
@jwt_required()
def admin_update_content():
    try:
        data = request.get_json()
        section = data.get('section')
        value = data.get('value')
        
        mongo.db.site_content.update_one(
            {'_id': 'main'},
            {'$set': {section: value}},
            upsert=True
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/content', methods=['GET'])
def get_public_content():
    try:
        content = mongo.db.site_content.find_one({'_id': 'main'})
        return jsonify({'content': serialize_doc(content) if content else {}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== ADMIN MANAGEMENT ==========
@app.route('/admin/admins', methods=['GET'])
@jwt_required()
def get_all_admins():
    try:
        admins = list(mongo.db.users.find({'role': {'$in': ['admin', 'super_admin']}}))
        return jsonify({
            'admins': [serialize_doc(a) for a in admins]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/admins', methods=['POST'])
@jwt_required()
def create_admin():
    try:
        data = request.get_json()
        
        # Check if email exists
        if mongo.db.users.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already exists'}), 400
        
        admin = {
            'username': data.get('full_name'),
            'email': data['email'],
            'password_hash': bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'role': data.get('role', 'admin'),
            'permissions': data.get('permissions', ['read', 'write']),
            'status': 'active',
            'created_at': datetime.utcnow()
        }
        result = mongo.db.users.insert_one(admin)
        admin['_id'] = str(result.inserted_id)
        return jsonify({
            'status': 'success',
            'admin': serialize_doc(admin)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/admins/<admin_id>', methods=['PUT'])
@jwt_required()
def update_admin(admin_id):
    try:
        data = request.get_json()
        update_data = {}
        
        if 'full_name' in data:
            update_data['username'] = data['full_name']
        if 'email' in data:
            update_data['email'] = data['email']
        if 'role' in data:
            update_data['role'] = data['role']
        if 'permissions' in data:
            update_data['permissions'] = data['permissions']
        if 'password' in data and data['password']:
            update_data['password_hash'] = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        mongo.db.users.update_one(
            {'_id': ObjectId(admin_id)},
            {'$set': update_data}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/admins/<admin_id>/status', methods=['PUT'])
@jwt_required()
def update_admin_status(admin_id):
    try:
        data = request.get_json()
        mongo.db.users.update_one(
            {'_id': ObjectId(admin_id)},
            {'$set': {'status': data.get('status')}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/admins/<admin_id>', methods=['DELETE'])
@jwt_required()
def delete_admin(admin_id):
    try:
        mongo.db.users.delete_one({'_id': ObjectId(admin_id)})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== SUPPORT TICKETS ==========
@app.route('/admin/support-tickets', methods=['GET'])
@jwt_required()
def admin_get_support_tickets():
    try:
        tickets = list(mongo.db.support_tickets.find().sort('created_at', -1))
        return jsonify({
            'tickets': [serialize_doc(t) for t in tickets]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/support-tickets/<ticket_id>', methods=['GET'])
@jwt_required()
def admin_get_support_ticket(ticket_id):
    try:
        ticket = mongo.db.support_tickets.find_one({'_id': ObjectId(ticket_id)})
        return jsonify({'ticket': serialize_doc(ticket)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/support-tickets/<ticket_id>/status', methods=['PUT'])
@jwt_required()
def admin_update_ticket_status(ticket_id):
    try:
        data = request.get_json()
        mongo.db.support_tickets.update_one(
            {'_id': ObjectId(ticket_id)},
            {'$set': {'status': data.get('status')}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/support-tickets/<ticket_id>/reply', methods=['POST'])
@jwt_required()
def admin_reply_to_ticket(ticket_id):
    try:
        data = request.get_json()
        reply = {
            'message': data.get('message'),
            'created_at': datetime.utcnow(),
            'admin': True
        }
        mongo.db.support_tickets.update_one(
            {'_id': ObjectId(ticket_id)},
            {'$push': {'replies': reply}}
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/support-tickets', methods=['POST'])
def create_support_ticket():
    try:
        data = request.get_json()
        ticket = {
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email'),
            'subject': data.get('subject'),
            'message': data.get('message'),
            'priority': data.get('priority', 'medium'),
            'status': 'open',
            'replies': [],
            'created_at': datetime.utcnow()
        }
        result = mongo.db.support_tickets.insert_one(ticket)
        return jsonify({
            'status': 'success',
            'ticket_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== PAYMENT METHODS ==========
@app.route('/payment-methods/<country>', methods=['GET'])
def get_payment_methods(country):
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
        'methods': methods
    })

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
        print("⚠️ Using in-memory storage (data will reset on restart)")
    
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
    print("   Email: info@queenkoba.com")
    print("   Password:N/A ")
    
    print("\n" + "="*70)
    print("   Starting API... (Press Ctrl+C to stop)")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
