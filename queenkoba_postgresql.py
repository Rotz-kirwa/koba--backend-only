from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import bcrypt
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS Configuration - Allow frontend and admin URLs
allowed_origins = [
    "http://localhost:8080",
    "http://localhost:5174",
    "http://localhost:3001",
    os.getenv('FRONTEND_URL', ''),
    os.getenv('ADMIN_URL', '')
]
allowed_origins = [origin for origin in allowed_origins if origin]  # Remove empty strings

CORS(app, resources={r"/*": {"origins": allowed_origins}})

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/queenkoba')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'queenkoba-super-secret-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize database on startup
@app.before_request
def initialize_database():
    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            db.create_all()
            seed_data()
            app.db_initialized = True

# ========== MODELS ==========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')
    country = db.Column(db.String(50), default='Kenya')
    preferred_currency = db.Column(db.String(10), default='KES')
    status = db.Column(db.String(20), default='active')
    permissions = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    base_price_usd = db.Column(db.Float, nullable=False)
    prices = db.Column(db.JSON)
    in_stock = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(500))
    discount_percentage = db.Column(db.Float, default=0)
    on_sale = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.Column(db.JSON)
    total_usd = db.Column(db.Float)
    shipping_address = db.Column(db.JSON)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    order_status = db.Column(db.String(20), default='processing')
    status_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    discount = db.Column(db.Float)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    uses = db.Column(db.Integer, default=0)
    limit = db.Column(db.Integer)
    expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(200))
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(120))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ShippingZone(db.Model):
    __tablename__ = 'shipping_zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    rate = db.Column(db.Float)
    currency = db.Column(db.String(10))
    delivery_days = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(120))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')
    replies = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteContent(db.Model):
    __tablename__ = 'site_content'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ========== HELPER FUNCTIONS ==========
def calculate_prices(base_price_usd):
    exchange_rates = {
        'KES': 128.5,
        'UGX': 3582.34,
        'BIF': 2850.0,
        'CDF': 2700.0
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

def seed_data():
    if Product.query.count() == 0:
        products = [
            Product(name='Complex Clarifier Cream', description='A luxurious cream that gently clarifies and purifies complexion', base_price_usd=29.99, category='Cream', in_stock=True, image_url='/images/cream.jpg'),
            Product(name='Complexion Clarifier Serum', description='Powerful serum with Vitamin C and Niacinamide', base_price_usd=34.50, category='Serum', in_stock=True, image_url='/images/serum.jpg'),
            Product(name='Complexion Clarifying Mask', description='Detoxifying clay mask with Charcoal and Tea Tree Oil', base_price_usd=25.75, category='Mask', in_stock=True, image_url='/images/mask.jpg'),
            Product(name='Complexion Renewal Scrub', description='Gentle exfoliating scrub with Jojoba beads', base_price_usd=21.99, category='Scrub', in_stock=True, image_url='/images/scrub.jpg'),
            Product(name='Rich Gentle Foaming Lather', description='Creamy foaming cleanser', base_price_usd=18.50, category='Cleanser', in_stock=True, image_url='/images/cleanser.jpg'),
            Product(name='Eternal Radiance Toner', description='Alcohol-free toner with Witch Hazel', base_price_usd=23.25, category='Toner', in_stock=True, image_url='/images/toner.jpg')
        ]
        
        for product in products:
            product.prices = calculate_prices(product.base_price_usd)
            db.session.add(product)
        
        db.session.commit()
        print(f"✅ Seeded {len(products)} products")
    
    if not User.query.filter_by(email='admin@queenkoba.com').first():
        admin = User(
            username='admin',
            email='admin@queenkoba.com',
            password_hash=bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8'),
            role='admin',
            permissions=['*']
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Created admin user: admin@queenkoba.com / admin123")

# ========== ROUTES ==========
@app.route('/')
def home():
    return jsonify({
        'api': 'Queen Koba Skincare',
        'version': '2.0',
        'database': 'PostgreSQL',
        'status': 'running'
    })

@app.route('/health')
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'counts': {
                'products': Product.query.count(),
                'users': User.query.count(),
                'orders': Order.query.count()
            }
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify({
        'status': 'success',
        'count': len(products),
        'products': [{
            '_id': str(p.id),
            'name': p.name,
            'description': p.description,
            'category': p.category,
            'base_price_usd': p.base_price_usd,
            'prices': p.prices,
            'in_stock': p.in_stock,
            'image_url': p.image_url,
            'discount_percentage': p.discount_percentage or 0,
            'on_sale': p.on_sale or False
        } for p in products]
    })

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'status': 'success',
        'product': {
            '_id': str(product.id),
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'base_price_usd': product.base_price_usd,
            'prices': product.prices,
            'in_stock': product.in_stock,
            'image_url': product.image_url
        }
    })

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'password', 'name', 'phone']):
        return jsonify({'message': 'Name, email, phone and password required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        password_hash=bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role='customer'
    )
    
    db.session.add(user)
    db.session.commit()
    
    token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'token': token,
        'user': {
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'phone': user.phone
        }
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email'], role='customer').first()
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'token': token,
        'user': {
            'id': str(user.id),
            'name': user.name or user.username,
            'email': user.email,
            'phone': user.phone or ''
        }
    })

@app.route('/auth/google', methods=['GET'])
def google_login():
    return jsonify({'message': 'Google OAuth not configured yet'}), 501

@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = int(get_jwt_identity())
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    total_usd = sum(item.product.base_price_usd * item.quantity for item in cart_items)
    
    return jsonify({
        'status': 'success',
        'cart': [{
            'product_id': str(item.product_id),
            'product_name': item.product.name,
            'product_price': item.product.base_price_usd,
            'quantity': item.quantity
        } for item in cart_items],
        'total': {'usd': round(total_usd, 2)}
    })

@app.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    product = Product.query.get_or_404(data['product_id'])
    
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=data['product_id']).first()
    
    if cart_item:
        cart_item.quantity += data['quantity']
    else:
        cart_item = CartItem(user_id=user_id, product_id=data['product_id'], quantity=data['quantity'])
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Product added to cart'})

@app.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total_usd = 0
    order_items = []
    
    for item in cart_items:
        item_total = item.product.base_price_usd * item.quantity
        total_usd += item_total
        order_items.append({
            'product_id': str(item.product_id),
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price_per_item': item.product.base_price_usd,
            'item_total': item_total
        })
    
    order = Order(
        order_id=str(uuid.uuid4())[:8].upper(),
        user_id=user_id,
        items=order_items,
        total_usd=total_usd,
        shipping_address=data.get('shipping_address', {}),
        payment_method=data.get('payment_method', 'card'),
        payment_status='pending',
        order_status='processing'
    )
    
    db.session.add(order)
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'order_id': order.order_id,
        'total': total_usd
    })

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'orders': [{
            '_id': str(o.id),
            'order_id': o.order_id,
            'items': o.items,
            'total_usd': o.total_usd,
            'order_status': o.order_status,
            'created_at': o.created_at.isoformat()
        } for o in orders]
    })

@app.route('/admin/auth/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'token': token,
        'user': {
            '_id': str(user.id),
            'email': user.email,
            'full_name': user.username or 'Admin',
            'role': user.role,
            'permissions': user.permissions or ['*']
        }
    })

@app.route('/admin/dashboard/kpis', methods=['GET'])
@jwt_required()
def get_dashboard_kpis():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_revenue = db.session.query(db.func.sum(Order.total_usd)).filter(
        Order.created_at >= thirty_days_ago,
        Order.payment_status == 'paid'
    ).scalar() or 0
    
    total_orders = Order.query.filter(Order.created_at >= thirty_days_ago).count()
    total_customers = User.query.filter_by(role='customer').count()
    
    return jsonify({
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'conversion_rate': 3.2,
        'low_stock_items': Product.query.filter_by(in_stock=False).count()
    })

@app.route('/admin/products', methods=['GET', 'POST'])
@jwt_required()
def admin_products():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify({
            'products': [{
                '_id': str(p.id),
                'name': p.name,
                'description': p.description,
                'category': p.category,
                'base_price_usd': p.base_price_usd,
                'prices': p.prices,
                'in_stock': p.in_stock
            } for p in products]
        })
    else:
        data = request.get_json()
        product = Product(**data)
        product.prices = calculate_prices(product.base_price_usd)
        db.session.add(product)
        db.session.commit()
        return jsonify({'status': 'success', 'product': {'_id': str(product.id)}}), 201

@app.route('/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        data = request.get_json()
        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        db.session.commit()
        return jsonify({'status': 'success'})

@app.route('/admin/orders', methods=['GET'])
@jwt_required()
def admin_get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    return jsonify({
        'orders': [{
            '_id': str(o.id),
            'order_id': o.order_id,
            'user_id': str(o.user_id),
            'total_usd': o.total_usd,
            'order_status': o.order_status,
            'created_at': o.created_at.isoformat()
        } for o in orders]
    })

@app.route('/admin/customers', methods=['GET'])
@jwt_required()
def admin_get_customers():
    customers = User.query.filter_by(role='customer').limit(50).all()
    return jsonify({
        'customers': [{
            '_id': str(c.id),
            'name': c.name or c.username,
            'email': c.email,
            'phone': c.phone,
            'created_at': c.created_at.isoformat()
        } for c in customers]
    })

@app.route('/admin/profile/password', methods=['PUT'])
@jwt_required()
def admin_change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    user = User.query.get_or_404(user_id)
    
    if not bcrypt.checkpw(data['current_password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    user.password_hash = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Password updated successfully'})

@app.route('/admin/reviews', methods=['GET'])
@jwt_required()
def admin_get_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return jsonify({
        'reviews': [{
            '_id': str(r.id),
            'product_id': str(r.product_id),
            'product_name': r.product_name,
            'customer_name': r.customer_name,
            'customer_email': r.customer_email,
            'rating': r.rating,
            'comment': r.comment,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in reviews]
    })

@app.route('/admin/reviews/<int:review_id>/approve', methods=['PUT'])
@jwt_required()
def admin_approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = 'approved'
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/reviews/<int:review_id>/reject', methods=['PUT'])
@jwt_required()
def admin_reject_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = 'rejected'
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/payment-methods/<country>', methods=['GET'])
def get_payment_methods(country):
    methods_map = {
        'Kenya': [
            {'name': 'M-Pesa', 'code': 'mpesa'},
            {'name': 'Airtel Money', 'code': 'airtel'},
            {'name': 'Visa/Mastercard', 'code': 'card'}
        ],
        'Uganda': [
            {'name': 'MTN Mobile Money', 'code': 'mtn'},
            {'name': 'Airtel Money', 'code': 'airtel'},
            {'name': 'Visa/Mastercard', 'code': 'card'}
        ]
    }
    
    return jsonify({
        'status': 'success',
        'country': country,
        'methods': methods_map.get(country, [])
    })

@app.route('/promotions/active', methods=['GET'])
def get_active_promotions():
    promotions = Promotion.query.filter_by(status='active').all()
    return jsonify({
        'promotions': [{
            '_id': str(p.id),
            'code': p.code,
            'discount': p.discount,
            'type': p.type,
            'expires': p.expires.isoformat() if p.expires else None
        } for p in promotions]
    })

@app.route('/promotions/validate', methods=['POST'])
def validate_promo_code():
    data = request.get_json()
    code = data.get('code', '').upper()
    
    promo = Promotion.query.filter_by(code=code, status='active').first()
    
    if not promo:
        return jsonify({'error': 'Invalid promo code'}), 404
    
    if promo.expires and promo.expires < datetime.utcnow():
        return jsonify({'error': 'Promo code expired'}), 400
    
    if promo.limit and promo.uses >= promo.limit:
        return jsonify({'error': 'Promo code limit reached'}), 400
    
    return jsonify({
        'code': promo.code,
        'discount': promo.discount,
        'type': promo.type
    })

@app.route('/support-tickets', methods=['POST'])
def create_support_ticket():
    data = request.get_json()
    ticket = SupportTicket(
        customer_name=data.get('customer_name'),
        customer_email=data.get('customer_email'),
        subject=data.get('subject'),
        message=data.get('message'),
        priority=data.get('priority', 'medium')
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'ticket_id': str(ticket.id)
    }), 201

@app.route('/admin/support-tickets', methods=['GET'])
@jwt_required()
def admin_get_support_tickets():
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return jsonify({
        'tickets': [{
            '_id': str(t.id),
            'customer_name': t.customer_name,
            'customer_email': t.customer_email,
            'subject': t.subject,
            'message': t.message,
            'priority': t.priority,
            'status': t.status,
            'created_at': t.created_at.isoformat()
        } for t in tickets]
    })

@app.route('/admin/promotions', methods=['GET', 'POST'])
@jwt_required()
def admin_promotions():
    if request.method == 'GET':
        promotions = Promotion.query.all()
        return jsonify({
            'promotions': [{
                '_id': str(p.id),
                'code': p.code,
                'discount': p.discount,
                'type': p.type,
                'status': p.status,
                'uses': p.uses,
                'limit': p.limit,
                'expires': p.expires.isoformat() if p.expires else None
            } for p in promotions]
        })
    else:
        data = request.get_json()
        promo = Promotion(
            code=data.get('code', '').upper(),
            discount=data.get('discount', 0),
            type=data.get('type', 'percentage'),
            status='active',
            limit=data.get('limit'),
            expires=data.get('expires')
        )
        db.session.add(promo)
        db.session.commit()
        return jsonify({'status': 'success'}), 201

@app.route('/admin/promotions/<int:promo_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/payments', methods=['GET'])
@jwt_required()
def admin_get_payments():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    payments = [{
        '_id': str(o.id),
        'order_id': o.order_id,
        'amount': o.total_usd,
        'payment_method': o.payment_method,
        'payment_status': o.payment_status,
        'created_at': o.created_at.isoformat()
    } for o in orders]
    return jsonify({'payments': payments})

@app.route('/admin/shipping-zones', methods=['GET', 'POST'])
@jwt_required()
def admin_shipping_zones():
    if request.method == 'GET':
        zones = ShippingZone.query.all()
        return jsonify({
            'zones': [{
                '_id': str(z.id),
                'name': z.name,
                'rate': z.rate,
                'currency': z.currency,
                'delivery_days': z.delivery_days,
                'active': z.active
            } for z in zones]
        })
    else:
        data = request.get_json()
        zone = ShippingZone(
            name=data.get('name'),
            rate=data.get('rate'),
            currency=data.get('currency', 'KES'),
            delivery_days=data.get('delivery_days'),
            active=True
        )
        db.session.add(zone)
        db.session.commit()
        return jsonify({'status': 'success'}), 201

@app.route('/admin/shipping-zones/<int:zone_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def admin_shipping_zone(zone_id):
    zone = ShippingZone.query.get_or_404(zone_id)
    if request.method == 'DELETE':
        db.session.delete(zone)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        data = request.get_json()
        for key, value in data.items():
            if hasattr(zone, key):
                setattr(zone, key, value)
        db.session.commit()
        return jsonify({'status': 'success'})

@app.route('/admin/content', methods=['GET', 'PUT'])
@jwt_required()
def admin_content():
    if request.method == 'GET':
        # Get all content from database
        all_content = SiteContent.query.all()
        content_dict = {c.key: c.value for c in all_content}
        
        # Return with defaults if not set
        return jsonify({
            'content': {
                'hero_title': content_dict.get('hero_title', 'Queen Koba Skincare'),
                'hero_subtitle': content_dict.get('hero_subtitle', 'Luxurious skincare for melanin-rich skin'),
                'about_title': content_dict.get('about_title', 'Our Story'),
                'about_description': content_dict.get('about_description', 'Queen Koba is dedicated to creating premium skincare products.'),
                'contact_email': content_dict.get('contact_email', 'info@queenkoba.com'),
                'contact_phone': content_dict.get('contact_phone', '0119 559 180'),
                'contact_whatsapp': content_dict.get('contact_whatsapp', '0119 559 180'),
                'instagram_handle': content_dict.get('instagram_handle', '@queenkoba'),
                'footer_text': content_dict.get('footer_text', '© 2024 Queen Koba. All rights reserved.')
            }
        })
    else:
        data = request.get_json()
        section = data.get('section')
        value = data.get('value')
        
        content = SiteContent.query.filter_by(key=section).first()
        if content:
            content.value = value
            content.updated_at = datetime.utcnow()
        else:
            content = SiteContent(key=section, value=value)
            db.session.add(content)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Content updated successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    
    print("\n" + "="*70)
    print("   🚀 QUEEN KOBA SKINCARE API - POSTGRESQL EDITION")
    print("="*70)
    print("✅ PostgreSQL connected")
    print("🌐 Server: http://0.0.0.0:5000")
    print("🔑 Admin: admin@queenkoba.com / admin123")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
