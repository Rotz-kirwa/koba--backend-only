from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta, timezone
from functools import wraps
import bcrypt
import uuid
import os
import base64
import json
from dotenv import load_dotenv
import requests

load_dotenv()

DEFAULT_GOOGLE_CLIENT_ID = '445338583811-0gknu3ni8fn9mh3pa874agtu61i29tvr.apps.googleusercontent.com'

app = Flask(__name__)

# CORS Configuration - Allow frontend and admin URLs
allowed_origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    os.getenv('FRONTEND_URL', ''),
    os.getenv('ADMIN_URL', ''),
]
extra_origins = os.getenv('CORS_ORIGINS', '')
if extra_origins:
    allowed_origins.extend([origin.strip() for origin in extra_origins.split(",") if origin.strip()])
allowed_origins = [origin for origin in allowed_origins if origin]

CORS(app, resources={r"/*": {"origins": allowed_origins}})

# Configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///queenkoba.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'queenkoba-super-secret-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize database on startup
@app.before_request
def initialize_database():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not hasattr(app, 'db_initialized'):
        with app.app_context():
            db.create_all()
            ensure_schema_updates()
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
    promotion_usages = db.relationship('PromotionUsage', backref='user', lazy=True)

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
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promotions.id'))
    promo_code = db.Column(db.String(50))
    discount_type = db.Column(db.String(20))
    discount_amount = db.Column(db.Float, default=0)
    shipping_discount = db.Column(db.Float, default=0)
    final_total_after_discount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    description = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    discount = db.Column(db.Float)
    type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    uses = db.Column(db.Integer, default=0)
    limit = db.Column(db.Integer)
    per_user_limit = db.Column(db.Integer)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float)
    first_order_only = db.Column(db.Boolean, default=False)
    starts_at = db.Column(db.DateTime)
    expires = db.Column(db.DateTime)
    applies_to_type = db.Column(db.String(20), default='all')
    customer_scope = db.Column(db.String(20), default='all')
    campaign_type = db.Column(db.String(50))
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_admin = db.relationship('User', foreign_keys=[created_by_admin_id])
    usages = db.relationship('PromotionUsage', backref='promotion', lazy=True, cascade='all, delete-orphan')
    product_links = db.relationship('PromotionProduct', backref='promotion', lazy=True, cascade='all, delete-orphan')
    category_links = db.relationship('PromotionCategory', backref='promotion', lazy=True, cascade='all, delete-orphan')
    user_links = db.relationship('PromotionUser', backref='promotion', lazy=True, cascade='all, delete-orphan')

class PromotionUsage(db.Model):
    __tablename__ = 'promotion_usages'
    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    discount_amount = db.Column(db.Float, default=0)
    shipping_discount = db.Column(db.Float, default=0)
    subtotal_kes = db.Column(db.Float, default=0)
    final_total_kes = db.Column(db.Float, default=0)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order')

class PromotionProduct(db.Model):
    __tablename__ = 'promotion_products'
    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    product = db.relationship('Product')

class PromotionCategory(db.Model):
    __tablename__ = 'promotion_categories'
    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)

class PromotionUser(db.Model):
    __tablename__ = 'promotion_users'
    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promotions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User')

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
def ensure_schema_updates():
    inspector = db.inspect(db.engine)
    table_names = set(inspector.get_table_names())
    columns_by_table = {
        table_name: {column['name'] for column in inspector.get_columns(table_name)}
        for table_name in table_names
    }

    required_columns = {
        'orders': {
            'promo_code_id': 'INTEGER',
            'promo_code': 'VARCHAR(50)',
            'discount_type': 'VARCHAR(20)',
            'discount_amount': 'FLOAT',
            'shipping_discount': 'FLOAT',
            'final_total_after_discount': 'FLOAT',
        },
        'promotions': {
            'description': 'TEXT',
            'internal_notes': 'TEXT',
            'per_user_limit': 'INTEGER',
            'min_order_amount': 'FLOAT',
            'max_discount_amount': 'FLOAT',
            'first_order_only': 'BOOLEAN',
            'starts_at': 'TIMESTAMP',
            'applies_to_type': 'VARCHAR(20)',
            'customer_scope': 'VARCHAR(20)',
            'campaign_type': 'VARCHAR(50)',
            'created_by_admin_id': 'INTEGER',
            'updated_at': 'TIMESTAMP',
        },
    }

    for table_name, columns in required_columns.items():
        if table_name not in table_names:
            continue

        existing_columns = columns_by_table.get(table_name, set())
        for column_name, sql_type in columns.items():
            if column_name in existing_columns:
                continue
            db.session.execute(
                db.text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}')
            )

    db.session.commit()

def serialize_datetime(value):
    return value.isoformat() if value else None

def parse_datetime_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value

    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed

def normalize_promo_code(code):
    return ''.join(str(code or '').split()).upper()

def normalize_category_name(category):
    return str(category or '').strip().lower()

def now_utc():
    return datetime.utcnow()

def parse_int(value, default=None):
    if value in (None, '', False):
        return default
    return int(value)

def parse_float(value, default=0):
    if value in (None, '', False):
        return default
    return float(value)

def generate_random_promo_code(prefix='QK', length=8):
    seed = uuid.uuid4().hex.upper()
    core = seed[:max(length, 4)]
    normalized_prefix = normalize_promo_code(prefix)[:8]
    return f"{normalized_prefix}{core}" if normalized_prefix else core

def promo_is_active(promo, current_time=None):
    current_time = current_time or now_utc()
    if not promo or promo.status != 'active':
        return False
    if promo.starts_at and promo.starts_at > current_time:
        return False
    if promo.expires and promo.expires < current_time:
        return False
    return True

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

def build_prices_from_kes(kes_amount):
    base_price_usd = kes_amount / 128.5
    prices = calculate_prices(base_price_usd)
    prices['KES']['amount'] = kes_amount
    return prices

def get_mpesa_base_url():
    env = os.getenv('M_PESA_ENV', 'production').lower()
    if env == 'sandbox':
        return 'https://sandbox.safaricom.co.ke'
    return 'https://api.safaricom.co.ke'

def get_mpesa_config():
    return {
        'consumer_key': os.getenv('M_PESA_CONSUMER_KEY', '').strip(),
        'consumer_secret': os.getenv('M_PESA_CONSUMER_SECRET', '').strip(),
        'shortcode': os.getenv('M_PESA_SHORTCODE', '').strip(),
        'passkey': os.getenv('M_PESA_PASSKEY', '').strip(),
        'callback_url': os.getenv('M_PESA_CALLBACK_URL', '').strip(),
        'transaction_type': os.getenv('M_PESA_TRANSACTION_TYPE', 'CustomerPayBillOnline').strip(),
        'account_reference': os.getenv('M_PESA_ACCOUNT_REFERENCE', 'QueenKoba').strip(),
        'timeout_seconds': int(os.getenv('M_PESA_TIMEOUT_SECONDS', '30') or 30),
    }

def mpesa_is_configured():
    config = get_mpesa_config()
    required = ['consumer_key', 'consumer_secret', 'shortcode', 'passkey', 'callback_url']
    return all(config.get(key) for key in required)

def get_mpesa_timestamp():
    return datetime.utcnow().strftime('%Y%m%d%H%M%S')

def build_mpesa_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode('utf-8')).decode('utf-8')

def normalize_mpesa_phone(phone_number):
    digits = ''.join(ch for ch in str(phone_number or '') if ch.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        digits = f"254{digits[1:]}"
    elif digits.startswith('7') and len(digits) == 9:
        digits = f"254{digits}"
    elif digits.startswith('1') and len(digits) == 9:
        digits = f"254{digits}"

    if len(digits) != 12 or not digits.startswith('254'):
        raise ValueError('M-Pesa phone number must be in the format 2547XXXXXXXX or 2541XXXXXXXX')

    return digits

def get_mpesa_access_token():
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise ValueError('M-Pesa is not fully configured. Set consumer key, consumer secret, shortcode, passkey, and callback URL.')

    credentials = f"{config['consumer_key']}:{config['consumer_secret']}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    response = requests.get(
        f"{get_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials",
        headers={'Authorization': f"Basic {encoded}"},
        timeout=config['timeout_seconds'],
    )
    response.raise_for_status()
    data = response.json()
    token = data.get('access_token')
    if not token:
        raise ValueError('Safaricom OAuth token missing from response')
    return token

def get_google_client_ids():
    raw_values = []
    for env_name in ('GOOGLE_CLIENT_IDS', 'GOOGLE_CLIENT_ID'):
        raw = os.getenv(env_name, '')
        if raw:
            raw_values.extend(raw.split(','))

    client_ids = [value.strip() for value in raw_values if value.strip()]
    if not client_ids:
        client_ids = [DEFAULT_GOOGLE_CLIENT_ID]

    return list(dict.fromkeys(client_ids))

def get_google_allowed_admin_emails():
    raw_values = []
    for env_name in ('GOOGLE_ALLOWED_EMAILS', 'ADMIN_GOOGLE_EMAILS', 'GOOGLE_ADMIN_EMAILS'):
        raw = os.getenv(env_name, '')
        if raw:
            raw_values.extend(raw.split(','))

    emails = [value.strip().lower() for value in raw_values if value.strip()]
    return list(dict.fromkeys(emails))

def build_customer_user_payload(user):
    return {
        'id': str(user.id),
        '_id': str(user.id),
        'name': user.name or user.username or user.email.split('@')[0],
        'username': user.username or user.name or user.email.split('@')[0],
        'email': user.email,
        'phone': user.phone or '',
        'country': user.country,
        'preferred_currency': user.preferred_currency,
        'role': user.role,
    }

def build_customer_auth_response(user, status_code=200):
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': token,
        'access_token': token,
        'user': build_customer_user_payload(user)
    }), status_code

def build_admin_user_payload(user):
    return {
        '_id': str(user.id),
        'email': user.email,
        'full_name': user.username or user.name or 'Admin',
        'role': user.role,
        'permissions': user.permissions or ['*']
    }

def build_admin_auth_response(user):
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': build_admin_user_payload(user)
    })

def get_current_user():
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return User.query.get(int(user_id))

def admin_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()

            if not user or user.role not in ['admin', 'super_admin'] or user.status != 'active':
                return jsonify({'error': 'Admin access required'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def verify_google_credential(credential):
    if not credential:
        raise ValueError('Google credential is required')

    try:
        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=10,
        )
        payload = response.json()
    except requests.RequestException:
        raise ValueError('Could not verify Google sign-in right now') from None
    except ValueError:
        raise ValueError('Google sign-in returned an invalid response') from None

    if response.status_code != 200:
        detail = payload.get('error_description') or payload.get('error') or 'Invalid Google credential'
        raise ValueError(detail)

    audience = (payload.get('aud') or '').strip()
    if audience not in get_google_client_ids():
        raise ValueError('Google sign-in does not match the configured client')

    email = (payload.get('email') or '').strip().lower()
    if not email:
        raise ValueError('Google sign-in did not return an email address')

    if str(payload.get('email_verified')).lower() != 'true':
        raise ValueError('A verified Google email is required to continue')

    return {
        'email': email,
        'name': (payload.get('name') or '').strip(),
        'given_name': (payload.get('given_name') or '').strip(),
        'sub': (payload.get('sub') or '').strip(),
    }

def get_or_create_google_admin_user(profile):
    email = profile['email']
    name = profile.get('name') or profile.get('given_name') or email.split('@')[0]
    allowed_emails = get_google_allowed_admin_emails()
    email_is_allowed = email in allowed_emails if allowed_emails else False

    user = User.query.filter_by(email=email).first()

    if user:
        if user.role not in ['admin', 'super_admin'] and not email_is_allowed:
            raise PermissionError('This Google account is not approved for admin access')

        if not user.name:
            user.name = name
        if not user.username:
            user.username = name
        if user.role not in ['admin', 'super_admin'] and email_is_allowed:
            user.role = 'admin'
            user.permissions = user.permissions or ['*']

        db.session.commit()
        return user

    if not email_is_allowed:
        raise PermissionError('This Google account is not approved for admin access')

    user = User(
        name=name,
        username=name,
        email=email,
        phone='',
        password_hash=bcrypt.hashpw(uuid.uuid4().hex.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role='admin',
        permissions=['*']
    )
    db.session.add(user)
    db.session.commit()
    return user

def get_or_create_google_customer_user(profile):
    email = profile['email']
    name = profile.get('name') or profile.get('given_name') or email.split('@')[0]

    user = User.query.filter_by(email=email).first()

    if user:
        if not user.name:
            user.name = name
        if not user.username:
            user.username = name
        if not user.phone:
            user.phone = ''
        db.session.commit()
        return user, False

    user = User(
        name=name,
        username=name,
        email=email,
        phone='',
        password_hash=bcrypt.hashpw(uuid.uuid4().hex.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role='customer',
        country='Kenya',
        preferred_currency='KES',
    )
    db.session.add(user)
    db.session.commit()
    return user, True

def get_optional_current_user():
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return None
    return get_current_user()

def build_order_item_payload(product, quantity):
    unit_price_usd = float(product.base_price_usd or 0)
    product_prices = product.prices or {}
    kes_entry = product_prices.get('KES') if isinstance(product_prices, dict) else None
    unit_price_kes = None
    if isinstance(kes_entry, dict):
        kes_amount = kes_entry.get('amount')
        if kes_amount is not None:
            unit_price_kes = float(kes_amount)
    if unit_price_kes is None:
        unit_price_kes = convert_usd_to_kes(unit_price_usd)

    quantity = int(quantity or 0)

    return {
        'product_id': str(product.id),
        'product_name': product.name,
        'product_price': unit_price_usd,
        'price_per_item': unit_price_usd,
        'product_price_kes': unit_price_kes,
        'price_per_item_kes': unit_price_kes,
        'description': product.description or '',
        'image_url': product.image_url,
        'category': product.category or '',
        'quantity': quantity,
        'item_total': round(unit_price_usd * quantity, 2),
        'item_total_kes': round(unit_price_kes * quantity, 2),
    }

def build_cart_item_payload(item):
    return build_order_item_payload(item.product, item.quantity)

def clear_user_cart_items(user_id):
    CartItem.query.filter_by(user_id=user_id).delete()

def get_promotion_product_ids(promo):
    return {int(link.product_id) for link in promo.product_links or []}

def get_promotion_categories(promo):
    return {
        normalize_category_name(link.category)
        for link in promo.category_links or []
        if normalize_category_name(link.category)
    }

def get_promotion_user_ids(promo):
    return {int(link.user_id) for link in promo.user_links or []}

def get_effective_order_count(user_id):
    if not user_id:
        return 0
    return Order.query.filter(
        Order.user_id == user_id,
        Order.order_status != 'payment_failed'
    ).count()

def get_promo_usage_count_for_user(promo_id, user_id):
    if not promo_id or not user_id:
        return 0
    return PromotionUsage.query.filter_by(promo_code_id=promo_id, user_id=user_id).count()

def build_promotion_payload(promo, include_stats=False):
    usage_stats = build_promotion_stats(promo) if include_stats else {}
    product_ids = sorted(get_promotion_product_ids(promo))
    categories = sorted(get_promotion_categories(promo))
    user_ids = sorted(get_promotion_user_ids(promo))
    usage_limit = int(promo.limit or 0) if promo.limit is not None else None
    used_count = int(promo.uses or 0)

    payload = {
        '_id': str(promo.id),
        'id': str(promo.id),
        'code': promo.code,
        'description': promo.description or '',
        'internal_notes': promo.internal_notes or '',
        'discount': float(promo.discount or 0),
        'discount_value': float(promo.discount or 0),
        'type': promo.type,
        'discount_type': promo.type,
        'status': promo.status,
        'is_active': promo.status == 'active',
        'uses': used_count,
        'used_count': used_count,
        'limit': usage_limit,
        'usage_limit': usage_limit,
        'remaining_uses': max(usage_limit - used_count, 0) if usage_limit is not None else None,
        'per_user_limit': promo.per_user_limit,
        'min_order_amount': float(promo.min_order_amount or 0),
        'max_discount_amount': float(promo.max_discount_amount or 0) if promo.max_discount_amount is not None else None,
        'first_order_only': bool(promo.first_order_only),
        'starts_at': serialize_datetime(promo.starts_at),
        'expires': serialize_datetime(promo.expires),
        'applies_to_type': promo.applies_to_type or 'all',
        'customer_scope': promo.customer_scope or 'all',
        'campaign_type': promo.campaign_type or '',
        'product_ids': product_ids,
        'categories': categories,
        'user_ids': user_ids,
        'created_by_admin_id': str(promo.created_by_admin_id) if promo.created_by_admin_id else None,
        'created_at': serialize_datetime(promo.created_at),
        'updated_at': serialize_datetime(promo.updated_at),
    }

    payload.update(usage_stats)
    return payload

def build_promotion_usage_payload(usage):
    order = usage.order
    return {
        '_id': str(usage.id),
        'user_id': str(usage.user_id),
        'order_id': str(usage.order_id),
        'order_reference': order.order_id if order else None,
        'discount_amount': float(usage.discount_amount or 0),
        'shipping_discount': float(usage.shipping_discount or 0),
        'subtotal_kes': float(usage.subtotal_kes or 0),
        'final_total_kes': float(usage.final_total_kes or 0),
        'used_at': serialize_datetime(usage.used_at),
    }

def build_promotion_stats(promo):
    usages = PromotionUsage.query.filter_by(promo_code_id=promo.id).all()
    total_discount_given = sum(float(usage.discount_amount or 0) + float(usage.shipping_discount or 0) for usage in usages)
    revenue_influenced = sum(float(usage.final_total_kes or 0) for usage in usages)
    orders_using_code = [build_promotion_usage_payload(usage) for usage in sorted(usages, key=lambda entry: entry.used_at or datetime.min, reverse=True)]

    return {
        'total_uses': len(usages),
        'total_discount_given': round(total_discount_given, 2),
        'revenue_influenced': round(revenue_influenced, 2),
        'orders_using_code': orders_using_code,
    }

def validate_promotion_payload(data):
    code = normalize_promo_code(data.get('code'))
    if not code:
        raise ValueError('Promo code is required')

    discount_type = str(data.get('discount_type') or data.get('type') or 'percentage').strip().lower()
    if discount_type not in ['percentage', 'fixed', 'free_shipping']:
        raise ValueError('Discount type must be percentage, fixed, or free_shipping')

    discount_value = parse_float(data.get('discount_value', data.get('discount', 0)), 0)
    if discount_type != 'free_shipping' and discount_value <= 0:
        raise ValueError('Discount value must be greater than zero')

    min_order_amount = parse_float(data.get('min_order_amount'), 0)
    max_discount_amount = data.get('max_discount_amount')
    max_discount_amount = parse_float(max_discount_amount, None) if max_discount_amount not in (None, '') else None
    usage_limit = parse_int(data.get('usage_limit', data.get('limit')), None)
    per_user_limit = parse_int(data.get('per_user_limit'), None)
    applies_to_type = str(data.get('applies_to_type') or 'all').strip().lower()
    if applies_to_type not in ['all', 'products', 'categories']:
        raise ValueError('Applies-to type must be all, products, or categories')

    customer_scope = str(data.get('customer_scope') or 'all').strip().lower()
    if customer_scope not in ['all', 'selected_users']:
        raise ValueError('Customer scope must be all or selected_users')

    starts_at = parse_datetime_value(data.get('starts_at'))
    expires = parse_datetime_value(data.get('expires'))
    if starts_at and expires and expires <= starts_at:
        raise ValueError('Expiry date must be after the start date')

    if discount_type == 'percentage' and discount_value > 100:
        raise ValueError('Percentage discounts cannot exceed 100')

    product_ids = sorted({int(product_id) for product_id in (data.get('product_ids') or []) if str(product_id).strip()})
    categories = sorted({normalize_category_name(category) for category in (data.get('categories') or []) if normalize_category_name(category)})
    user_ids = sorted({int(user_id) for user_id in (data.get('user_ids') or []) if str(user_id).strip()})

    if applies_to_type == 'products' and not product_ids:
        raise ValueError('Select at least one product for product-specific promotions')
    if applies_to_type == 'categories' and not categories:
        raise ValueError('Select at least one category for category-specific promotions')
    if customer_scope == 'selected_users' and not user_ids:
        raise ValueError('Select at least one user for targeted promotions')

    return {
        'code': code,
        'description': str(data.get('description') or '').strip(),
        'internal_notes': str(data.get('internal_notes') or '').strip(),
        'discount': discount_value,
        'type': discount_type,
        'status': 'active' if bool(data.get('is_active', data.get('status', 'active') == 'active')) else 'inactive',
        'limit': usage_limit,
        'per_user_limit': per_user_limit,
        'min_order_amount': min_order_amount,
        'max_discount_amount': max_discount_amount,
        'first_order_only': bool(data.get('first_order_only')),
        'starts_at': starts_at,
        'expires': expires,
        'applies_to_type': applies_to_type,
        'customer_scope': customer_scope,
        'campaign_type': str(data.get('campaign_type') or '').strip(),
        'product_ids': product_ids,
        'categories': categories,
        'user_ids': user_ids,
    }

def sync_promotion_targets(promo, payload):
    PromotionProduct.query.filter_by(promo_code_id=promo.id).delete()
    PromotionCategory.query.filter_by(promo_code_id=promo.id).delete()
    PromotionUser.query.filter_by(promo_code_id=promo.id).delete()

    for product_id in payload['product_ids']:
        db.session.add(PromotionProduct(promo_code_id=promo.id, product_id=product_id))

    for category in payload['categories']:
        db.session.add(PromotionCategory(promo_code_id=promo.id, category=category))

    for user_id in payload['user_ids']:
        db.session.add(PromotionUser(promo_code_id=promo.id, user_id=user_id))

def apply_promotion_model_updates(promo, payload, admin_user_id=None):
    promo.code = payload['code']
    promo.description = payload['description']
    promo.internal_notes = payload['internal_notes']
    promo.discount = payload['discount']
    promo.type = payload['type']
    promo.status = payload['status']
    promo.limit = payload['limit']
    promo.per_user_limit = payload['per_user_limit']
    promo.min_order_amount = payload['min_order_amount']
    promo.max_discount_amount = payload['max_discount_amount']
    promo.first_order_only = payload['first_order_only']
    promo.starts_at = payload['starts_at']
    promo.expires = payload['expires']
    promo.applies_to_type = payload['applies_to_type']
    promo.customer_scope = payload['customer_scope']
    promo.campaign_type = payload['campaign_type']
    if admin_user_id and not promo.created_by_admin_id:
        promo.created_by_admin_id = admin_user_id

def build_checkout_items_from_payload(payload_items):
    order_items = []
    for raw_item in payload_items or []:
        product_id = parse_int(raw_item.get('product_id'))
        quantity = parse_int(raw_item.get('quantity'), 1)
        if not product_id or quantity < 1:
            continue

        product = Product.query.get(product_id)
        if not product:
            raise ValueError(f'Product {product_id} no longer exists')
        order_items.append(build_order_item_payload(product, quantity))

    return order_items

def resolve_order_items_for_promo_request(user, data):
    payload_items = build_checkout_items_from_payload(data.get('items') or [])
    if payload_items:
        return payload_items

    if user:
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        if cart_items:
            return [build_cart_item_payload(item) for item in cart_items]

    raise ValueError('Add items to your cart before applying a promo code')

def resolve_order_items_for_checkout(user_id, data):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if cart_items:
        return [build_cart_item_payload(item) for item in cart_items]

    payload_items = build_checkout_items_from_payload(data.get('items') or [])
    if payload_items:
        return payload_items

    raise ValueError('Cart is empty')

def resolve_shipping_kes(data):
    delivery = data.get('delivery') or {}
    totals = data.get('totals') or {}
    return max(parse_float(delivery.get('shipping_fee', totals.get('shipping_kes')), 0), 0)

def evaluate_promotion(promo, user, order_items, shipping_kes):
    current_time = now_utc()
    normalized_code = promo.code if promo else ''
    subtotal_kes = round(sum(float(item.get('item_total_kes', 0) or 0) for item in order_items), 2)

    if not promo:
        raise ValueError('Invalid promo code')

    if not promo_is_active(promo, current_time=current_time):
        raise ValueError('This promo code is inactive or outside its valid date range')

    if promo.limit is not None and int(promo.uses or 0) >= int(promo.limit):
        raise ValueError('This promo code has reached its usage limit')

    if promo.customer_scope == 'selected_users':
        if not user:
            raise ValueError('Sign in to use this promo code')
        if user.id not in get_promotion_user_ids(promo):
            raise ValueError('This promo code is not available for your account')

    if promo.first_order_only:
        if not user:
            raise ValueError('Sign in to use this first-order promo code')
        if get_effective_order_count(user.id) > 0:
            raise ValueError('This promo code is only available on your first order')

    if promo.per_user_limit is not None:
        if not user:
            raise ValueError('Sign in to use this promo code')
        if get_promo_usage_count_for_user(promo.id, user.id) >= int(promo.per_user_limit):
            raise ValueError('You have already used this promo code the maximum number of times')

    if promo.min_order_amount and subtotal_kes < float(promo.min_order_amount):
        raise ValueError(f'This promo code requires a minimum order of KSh {float(promo.min_order_amount):,.0f}')

    eligible_items = list(order_items)
    if promo.applies_to_type == 'products':
        target_ids = get_promotion_product_ids(promo)
        eligible_items = [item for item in order_items if parse_int(item.get('product_id')) in target_ids]
    elif promo.applies_to_type == 'categories':
        target_categories = get_promotion_categories(promo)
        eligible_items = [
            item for item in order_items
            if normalize_category_name(item.get('category')) in target_categories
        ]

    eligible_subtotal_kes = round(sum(float(item.get('item_total_kes', 0) or 0) for item in eligible_items), 2)
    if promo.applies_to_type != 'all' and eligible_subtotal_kes <= 0:
        raise ValueError('This promo code does not apply to the current cart')

    discount_amount = 0
    shipping_discount = 0

    if promo.type == 'percentage':
        discount_amount = round(eligible_subtotal_kes * (float(promo.discount or 0) / 100), 2)
        if promo.max_discount_amount is not None:
            discount_amount = min(discount_amount, float(promo.max_discount_amount))
    elif promo.type == 'fixed':
        discount_amount = min(round(float(promo.discount or 0), 2), eligible_subtotal_kes)
    elif promo.type == 'free_shipping':
        shipping_discount = round(max(float(shipping_kes or 0), 0), 2)

    discount_amount = min(discount_amount, subtotal_kes)
    shipping_discount = min(shipping_discount, max(float(shipping_kes or 0), 0))
    final_total_kes = max(round(subtotal_kes + float(shipping_kes or 0) - discount_amount - shipping_discount, 2), 0)

    return {
        'promo_code_id': promo.id,
        'promo_code': normalized_code,
        'code': normalized_code,
        'description': promo.description or '',
        'campaign_type': promo.campaign_type or '',
        'discount_type': promo.type,
        'discount_value': float(promo.discount or 0),
        'discount_amount': round(discount_amount, 2),
        'shipping_discount': round(shipping_discount, 2),
        'subtotal_kes': subtotal_kes,
        'eligible_subtotal_kes': eligible_subtotal_kes,
        'shipping_kes': round(float(shipping_kes or 0), 2),
        'final_total_kes': final_total_kes,
        'applies_to_type': promo.applies_to_type or 'all',
        'customer_scope': promo.customer_scope or 'all',
        'first_order_only': bool(promo.first_order_only),
        'message': 'Promo code applied successfully',
    }

def resolve_promotion_for_checkout(user, data, order_items, shipping_kes):
    code = normalize_promo_code(data.get('promo_code'))
    if not code:
        subtotal_kes = round(sum(float(item.get('item_total_kes', 0) or 0) for item in order_items), 2)
        return {
            'promo_code_id': None,
            'promo_code': '',
            'code': '',
            'discount_type': None,
            'discount_value': 0,
            'discount_amount': 0,
            'shipping_discount': 0,
            'subtotal_kes': subtotal_kes,
            'eligible_subtotal_kes': subtotal_kes,
            'shipping_kes': round(float(shipping_kes or 0), 2),
            'final_total_kes': round(subtotal_kes + float(shipping_kes or 0), 2),
            'message': '',
        }

    promo = Promotion.query.filter_by(code=code).first()
    return evaluate_promotion(promo, user, order_items, shipping_kes)

def record_promotion_usage_for_order(order):
    if not order or not order.promo_code_id or not order.user_id:
        return

    existing = PromotionUsage.query.filter_by(order_id=order.id).first()
    if existing:
        return

    promo = Promotion.query.get(order.promo_code_id)
    if not promo:
        return

    state = get_order_payment_state(order)
    totals = state.get('totals', {}) if isinstance(state, dict) else {}
    usage = PromotionUsage(
        promo_code_id=promo.id,
        user_id=order.user_id,
        order_id=order.id,
        discount_amount=float(order.discount_amount or totals.get('discount_amount', 0) or 0),
        shipping_discount=float(order.shipping_discount or totals.get('shipping_discount', 0) or 0),
        subtotal_kes=float(totals.get('subtotal_kes', 0) or 0),
        final_total_kes=float(order.final_total_after_discount or totals.get('grand_total_kes', 0) or 0),
    )
    db.session.add(usage)
    promo.uses = int(promo.uses or 0) + 1

def get_order_payment_state(order):
    if not order.status_note:
        return {}

    try:
        return json.loads(order.status_note)
    except (TypeError, json.JSONDecodeError):
        return {}

def get_order_note(order):
    if not order.status_note:
        return None

    state = get_order_payment_state(order)
    if state:
        return state.get('note')

    return order.status_note

def set_order_payment_state(order, **updates):
    state = get_order_payment_state(order)
    state.update(updates)
    order.status_note = json.dumps(state)
    return state

def append_order_event(order, event_type, message, category='order', actor='system', metadata=None):
    state = get_order_payment_state(order)
    events = list(state.get('events') or [])
    events.append({
        'type': event_type,
        'category': category,
        'message': message,
        'actor': actor,
        'metadata': metadata or {},
        'created_at': datetime.utcnow().isoformat(),
    })
    state['events'] = events[-50:]
    state['last_event_at'] = events[-1]['created_at']
    order.status_note = json.dumps(state)
    return state

def build_order_summary_payload(data, user, order_items, total_usd, promo_summary):
    payment_details = data.get('payment_details') or {}
    delivery = data.get('delivery') or {}
    subtotal_kes = float(promo_summary.get('subtotal_kes', 0) or 0)
    shipping_kes = float(promo_summary.get('shipping_kes', 0) or 0)
    discount_amount = float(promo_summary.get('discount_amount', 0) or 0)
    shipping_discount = float(promo_summary.get('shipping_discount', 0) or 0)
    grand_total_kes = float(promo_summary.get('final_total_kes', subtotal_kes + shipping_kes) or 0)
    discount_percent = float(promo_summary.get('discount_value', 0) or 0) if promo_summary.get('discount_type') == 'percentage' else 0

    return {
        'customer': {
            'user_id': str(user.id) if user else None,
            'name': (data.get('shipping_address') or {}).get('name') or (user.name if user else None) or (user.username if user else None),
            'email': (data.get('shipping_address') or {}).get('email') or (user.email if user else None),
            'phone': (data.get('shipping_address') or {}).get('phone') or (user.phone if user else None),
        },
        'totals': {
            'currency': 'KES',
            'subtotal_kes': subtotal_kes,
            'shipping_kes': shipping_kes,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'shipping_discount': shipping_discount,
            'total_discount': round(discount_amount + shipping_discount, 2),
            'grand_total_kes': grand_total_kes,
            'total_usd': total_usd,
        },
        'promo': {
            'promo_code_id': promo_summary.get('promo_code_id'),
            'promo_code': promo_summary.get('promo_code'),
            'discount_type': promo_summary.get('discount_type'),
            'discount_value': promo_summary.get('discount_value'),
            'discount_amount': discount_amount,
            'shipping_discount': shipping_discount,
            'campaign_type': promo_summary.get('campaign_type'),
            'description': promo_summary.get('description'),
        },
        'payment_details': payment_details,
        'delivery': delivery,
    }

def convert_usd_to_kes(amount):
    return round(float(amount or 0) * 128.5, 2)

def normalize_order_items_for_admin(items):
    normalized_items = []
    for item in items or []:
        normalized = dict(item)
        quantity = int(normalized.get('quantity', 1) or 1)

        if normalized.get('price_per_item_kes') is None and normalized.get('price_per_item') is not None:
            normalized['price_per_item_kes'] = convert_usd_to_kes(normalized.get('price_per_item'))

        if normalized.get('item_total_kes') is None:
            if normalized.get('item_total') is not None:
                normalized['item_total_kes'] = convert_usd_to_kes(normalized.get('item_total'))
            else:
                normalized['item_total_kes'] = float(normalized.get('price_per_item_kes', 0) or 0) * quantity

        normalized_items.append(normalized)

    return normalized_items

def resolve_order_totals_kes(order, state, items):
    totals = state.get('totals', {}) if isinstance(state, dict) else {}

    subtotal_kes = float(totals.get('subtotal_kes', 0) or 0)
    shipping_kes = float(totals.get('shipping_kes', 0) or 0)
    grand_total_kes = float(totals.get('grand_total_kes', 0) or 0)
    amount_kes = float(state.get('amount_kes', 0) or 0) if isinstance(state, dict) else 0

    items_subtotal_kes = sum(float(item.get('item_total_kes', 0) or 0) for item in items)
    converted_total_usd_kes = convert_usd_to_kes(order.total_usd) if order.total_usd else 0

    if subtotal_kes <= 0:
        subtotal_kes = items_subtotal_kes

    if grand_total_kes <= 0 and order.final_total_after_discount:
        grand_total_kes = float(order.final_total_after_discount or 0)

    if grand_total_kes <= 0:
        if amount_kes > 0:
            grand_total_kes = amount_kes
        elif subtotal_kes > 0 or shipping_kes > 0:
            grand_total_kes = subtotal_kes + shipping_kes
        elif converted_total_usd_kes > 0:
            grand_total_kes = converted_total_usd_kes

    if grand_total_kes > 0 and grand_total_kes < 1 and converted_total_usd_kes > 0:
        grand_total_kes = converted_total_usd_kes

    if subtotal_kes <= 0 and grand_total_kes > 0:
        subtotal_kes = max(grand_total_kes - shipping_kes, 0)

    return subtotal_kes, shipping_kes, grand_total_kes

def resolve_payment_status(order, state):
    if order.payment_method != 'mpesa':
        return order.payment_status or 'pending'

    result_code = state.get('result_code') if isinstance(state, dict) else None
    receipt_number = state.get('receipt_number') if isinstance(state, dict) else None

    if receipt_number or str(result_code) == '0':
        return 'paid'

    if str(result_code) in {'1', '1032', '1037', '2001'} or order.order_status == 'payment_failed':
        return 'failed'

    if order.payment_status in {'initiated', 'pending', 'failed'}:
        return order.payment_status

    if order.payment_status == 'paid':
        return 'pending'

    return order.payment_status or 'pending'

def build_admin_order_payload(order):
    state = get_order_payment_state(order)
    customer = state.get('customer', {}) if isinstance(state, dict) else {}
    payment_details = state.get('payment_details', {}) if isinstance(state, dict) else {}
    delivery = state.get('delivery', {}) if isinstance(state, dict) else {}
    promo = state.get('promo', {}) if isinstance(state, dict) else {}
    receipt_number = state.get('receipt_number')
    events = list(state.get('events') or [])
    items = normalize_order_items_for_admin(order.items or [])
    subtotal_kes, shipping_kes, grand_total_kes = resolve_order_totals_kes(order, state, items)

    shipping_address = order.shipping_address or {}
    customer_name = customer.get('name') or shipping_address.get('name') or (order.user.name if order.user else None) or (order.user.username if order.user else None)
    customer_email = customer.get('email') or shipping_address.get('email') or (order.user.email if order.user else None)
    customer_phone = customer.get('phone') or shipping_address.get('phone') or (order.user.phone if order.user else None)
    payment_status = resolve_payment_status(order, state)

    return {
        '_id': str(order.id),
        'order_id': order.order_id,
        'user_id': str(order.user_id),
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'items': items,
        'shipping_address': shipping_address,
        'delivery': delivery,
        'payment_method': order.payment_method,
        'payment_status': payment_status,
        'payment_details': payment_details,
        'payment_receipt': receipt_number,
        'payment_state': state,
        'events': events,
        'last_event': events[-1] if events else None,
        'order_status': order.order_status,
        'status_note': get_order_note(order),
        'subtotal_kes': subtotal_kes,
        'shipping_kes': shipping_kes,
        'grand_total_kes': grand_total_kes,
        'discount_percent': float((state.get('totals') or {}).get('discount_percent', 0) or 0),
        'promo_code_id': str(order.promo_code_id) if order.promo_code_id else promo.get('promo_code_id'),
        'promo_code': order.promo_code or promo.get('promo_code'),
        'discount_type': order.discount_type or promo.get('discount_type'),
        'discount_amount': float(order.discount_amount or (state.get('totals') or {}).get('discount_amount', 0) or 0),
        'shipping_discount': float(order.shipping_discount or (state.get('totals') or {}).get('shipping_discount', 0) or 0),
        'final_total_after_discount': float(order.final_total_after_discount or grand_total_kes),
        'promo': promo,
        'total_usd': order.total_usd,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat() if order.updated_at else None,
    }

def find_order_by_checkout_request_id(checkout_request_id):
    if not checkout_request_id:
        return None

    orders = Order.query.filter_by(payment_method='mpesa').order_by(Order.created_at.desc()).all()
    for order in orders:
      state = get_order_payment_state(order)
      if state.get('checkout_request_id') == checkout_request_id:
          return order
    return None

def start_mpesa_stk_push(phone_number, amount_kes, order, description='Queen Koba order payment'):
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise ValueError('M-Pesa is not fully configured. Set consumer key, consumer secret, shortcode, passkey, and callback URL.')

    normalized_phone = normalize_mpesa_phone(phone_number)
    timestamp = get_mpesa_timestamp()
    token = get_mpesa_access_token()
    payload = {
        'BusinessShortCode': config['shortcode'],
        'Password': build_mpesa_password(config['shortcode'], config['passkey'], timestamp),
        'Timestamp': timestamp,
        'TransactionType': config['transaction_type'],
        'Amount': int(round(amount_kes)),
        'PartyA': normalized_phone,
        'PartyB': config['shortcode'],
        'PhoneNumber': normalized_phone,
        'CallBackURL': config['callback_url'],
        'AccountReference': order.order_id or config['account_reference'],
        'TransactionDesc': description[:182],
    }
    response = requests.post(
        f"{get_mpesa_base_url()}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={'Authorization': f"Bearer {token}"},
        timeout=config['timeout_seconds'],
    )
    response.raise_for_status()
    return response.json(), normalized_phone

def query_mpesa_stk_status(checkout_request_id):
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise ValueError('M-Pesa is not fully configured. Set consumer key, consumer secret, shortcode, passkey, and callback URL.')

    timestamp = get_mpesa_timestamp()
    token = get_mpesa_access_token()
    payload = {
        'BusinessShortCode': config['shortcode'],
        'Password': build_mpesa_password(config['shortcode'], config['passkey'], timestamp),
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    response = requests.post(
        f"{get_mpesa_base_url()}/mpesa/stkpushquery/v1/query",
        json=payload,
        headers={'Authorization': f"Bearer {token}"},
        timeout=config['timeout_seconds'],
    )
    response.raise_for_status()
    return response.json()

def extract_mpesa_callback_metadata(callback_metadata):
    items = callback_metadata.get('Item', []) if isinstance(callback_metadata, dict) else []
    metadata = {}
    for item in items:
        name = item.get('Name')
        if name:
            metadata[name] = item.get('Value')
    return metadata

def build_mpesa_status_response(order):
    state = get_order_payment_state(order)
    return {
        'order_id': order.order_id,
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'order_status': order.order_status,
        'checkout_request_id': state.get('checkout_request_id'),
        'merchant_request_id': state.get('merchant_request_id'),
        'result_code': state.get('result_code'),
        'result_desc': state.get('result_desc'),
        'customer_message': state.get('customer_message'),
        'receipt_number': state.get('receipt_number'),
        'phone_number': state.get('phone_number'),
        'amount_kes': state.get('amount_kes'),
        'query_error': state.get('query_error'),
    }

def is_valid_customer_password(password):
    return isinstance(password, str) and password.isdigit() and len(password) == 4

def seed_data():
    product_catalog = [
        {
            'name': 'Complexion Clarifying Cleanser 120ml',
            'description': 'Erase impurities without stripping moisture. African botanicals gently clarify and prep skin for brighter tone. Feel fresh, confident, and ready to glow.',
            'base_price_usd': 1899 / 128.5,
            'category': 'Cleanser',
            'image_url': 'https://www.dropbox.com/scl/fi/4tulvx5wuscmhcrvls4tg/sp2.jpeg?rlkey=6lr1shzfkfy14xcl6d7zhqxmd&st=uec69ia4&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(1899),
        },
        {
            'name': 'Brightening Toner 120ml',
            'description': 'Mist away dullness and balance tone with licorice root and aloe. Soothes instantly and reveals even radiance. Your daily step to luminous skin.',
            'base_price_usd': 1999 / 128.5,
            'category': 'Toner',
            'image_url': 'https://www.dropbox.com/scl/fi/akek115wovbezb0m923q0/sp3.jpeg?rlkey=w25aqom0rmq40uwmqse84cawb&st=vb6mzc2a&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(1999),
        },
        {
            'name': 'Complexion Clarifying Serum 30ml',
            'description': 'Target dark spots and hyperpigmentation with liwa and moringa. Fade unevenness and unlock up to 2 shades brighter glow. Feel empowered and radiant.',
            'base_price_usd': 2499 / 128.5,
            'category': 'Serum',
            'image_url': 'https://www.dropbox.com/scl/fi/ydx5ia5xvcblz5a7d8ty2/sp4.jpeg?rlkey=jy5lypf5j1csv88fy7s33pte9&st=r8air5om&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(2499),
        },
        {
            'name': 'Complexion Clarifying Cream 50ml',
            'description': 'Deeply hydrate and plump with shea and snail mucin. Lock in brightness, smooth texture, and boost lasting confidence.',
            'base_price_usd': 2399 / 128.5,
            'category': 'Cream',
            'image_url': 'https://www.dropbox.com/scl/fi/bparrxju6nzi3y816yoc7/sp5.jpeg?rlkey=mae29d7hd4dq88lj4hlvf8fju&st=yqb89dwv&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(2399),
        },
        {
            'name': 'Brightening Face Mask 120ml',
            'description': 'Weekly reset: Qasil + aloe clarify and brighten, reduce dullness for high-end glow. Pamper yourself to self-love.',
            'base_price_usd': 1499 / 128.5,
            'category': 'Mask',
            'image_url': 'https://www.dropbox.com/scl/fi/srxgy8id5smigxy8vtepg/sp6.jpeg?rlkey=4s4p1hq245l9htmf3952f0xnb&st=9jgl6wjw&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(1499),
        },
        {
            'name': 'Full Product Kit',
            'description': 'Mask, toner, serum, cream, and cleanser together in one complete routine. The full kit for brighter, even, melanin-safe radiance.',
            'base_price_usd': 9999 / 128.5,
            'category': 'Bundle',
            'image_url': 'https://www.dropbox.com/scl/fi/jpdncaq9lkmtnhxz3xbli/new.jpeg?rlkey=y6gg1oiji39i52ve9avevqplh&st=zuyfr36d&raw=1',
            'discount_percentage': 0,
            'on_sale': False,
            'prices': build_prices_from_kes(9999),
        },
    ]

    # Hard-sync catalog to match the initial main-site products.
    # Any legacy products not in this category set are removed.
    categories = {item['category'] for item in product_catalog}
    for existing in Product.query.all():
        if existing.category not in categories:
            db.session.delete(existing)

    synced = 0
    for item in product_catalog:
        matches = Product.query.filter_by(category=item['category']).order_by(Product.id.asc()).all()
        product = matches[0] if matches else None

        # Remove duplicates for same category, keep first.
        if len(matches) > 1:
            for duplicate in matches[1:]:
                db.session.delete(duplicate)

        if product:
            product.name = item['name']
            product.description = item['description']
            product.base_price_usd = item['base_price_usd']
            product.image_url = item['image_url']
            product.in_stock = True
            product.discount_percentage = item.get('discount_percentage', 0)
            product.on_sale = item.get('on_sale', False)
        else:
            product = Product(
                name=item['name'],
                description=item['description'],
                base_price_usd=item['base_price_usd'],
                category=item['category'],
                in_stock=True,
                image_url=item['image_url'],
                discount_percentage=item.get('discount_percentage', 0),
                on_sale=item.get('on_sale', False),
            )
            db.session.add(product)

        product.prices = item.get('prices', calculate_prices(product.base_price_usd))
        synced += 1

    db.session.commit()
    print(f"✅ Synced {synced} products")
    
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

    admin_user = User.query.filter_by(email='admin@queenkoba.com').first()
    seeded_promotions = [
        {
            'code': 'WELCOME10',
            'description': '10% off for first-time Queen Koba customers',
            'internal_notes': 'Welcome journey code',
            'discount': 10,
            'type': 'percentage',
            'status': 'active',
            'limit': 1000,
            'per_user_limit': 1,
            'min_order_amount': 1500,
            'max_discount_amount': 1000,
            'first_order_only': True,
            'starts_at': now_utc() - timedelta(days=1),
            'expires': now_utc() + timedelta(days=180),
            'applies_to_type': 'all',
            'customer_scope': 'all',
            'campaign_type': 'welcome',
        },
        {
            'code': 'FREEDELIVERY',
            'description': 'Free shipping across Kenya for limited-time campaigns',
            'internal_notes': 'Shipping incentive code',
            'discount': 0,
            'type': 'free_shipping',
            'status': 'active',
            'limit': 500,
            'per_user_limit': 3,
            'min_order_amount': 2500,
            'max_discount_amount': None,
            'first_order_only': False,
            'starts_at': now_utc() - timedelta(days=1),
            'expires': now_utc() + timedelta(days=90),
            'applies_to_type': 'all',
            'customer_scope': 'all',
            'campaign_type': 'cart_recovery',
        },
        {
            'code': 'MELANIN15',
            'description': '15% off selected glow essentials',
            'internal_notes': 'Category-focused seasonal boost',
            'discount': 15,
            'type': 'percentage',
            'status': 'active',
            'limit': 300,
            'per_user_limit': 2,
            'min_order_amount': 2000,
            'max_discount_amount': 1500,
            'first_order_only': False,
            'starts_at': now_utc() - timedelta(days=1),
            'expires': now_utc() + timedelta(days=120),
            'applies_to_type': 'categories',
            'customer_scope': 'all',
            'campaign_type': 'holiday_sale',
            'categories': ['serum', 'cream'],
        },
    ]

    for seeded in seeded_promotions:
        promo = Promotion.query.filter_by(code=seeded['code']).first()
        payload = {
            'code': seeded['code'],
            'description': seeded['description'],
            'internal_notes': seeded['internal_notes'],
            'discount_value': seeded['discount'],
            'discount_type': seeded['type'],
            'is_active': seeded['status'] == 'active',
            'usage_limit': seeded['limit'],
            'per_user_limit': seeded['per_user_limit'],
            'min_order_amount': seeded['min_order_amount'],
            'max_discount_amount': seeded['max_discount_amount'],
            'first_order_only': seeded['first_order_only'],
            'starts_at': seeded['starts_at'],
            'expires': seeded['expires'],
            'applies_to_type': seeded.get('applies_to_type', 'all'),
            'customer_scope': seeded.get('customer_scope', 'all'),
            'campaign_type': seeded.get('campaign_type', ''),
            'categories': seeded.get('categories', []),
            'product_ids': seeded.get('product_ids', []),
            'user_ids': seeded.get('user_ids', []),
        }
        validated = validate_promotion_payload(payload)
        if not promo:
            promo = Promotion(created_by_admin_id=admin_user.id if admin_user else None)
            db.session.add(promo)
            db.session.flush()
        apply_promotion_model_updates(promo, validated, admin_user_id=admin_user.id if admin_user else None)
        sync_promotion_targets(promo, validated)

    db.session.commit()

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
    data = request.get_json() or {}

    if not all(k in data and data.get(k) for k in ['email', 'password', 'name', 'phone']):
        return jsonify({'message': 'Name, email, phone and password required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    if not is_valid_customer_password(data['password']):
        return jsonify({'message': 'Password must be exactly 4 digits'}), 400

    user = User(
        name=data['name'],
        username=data.get('username', data['name']),
        email=data['email'],
        phone=data['phone'],
        password_hash=bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role='customer',
        country=data.get('country', 'Kenya'),
        preferred_currency=data.get('preferred_currency', 'KES'),
    )

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        'status': 'success',
        'message': 'Registration successful',
        'token': token,
        'access_token': token,
        'user': {
            'id': str(user.id),
            '_id': str(user.id),
            'name': user.name,
            'username': user.username or user.name,
            'email': user.email,
            'phone': user.phone,
            'country': user.country,
            'preferred_currency': user.preferred_currency,
            'role': user.role,
        }
    }), 201

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username') or data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Username, email and password required'}), 400

    if not is_valid_customer_password(password):
        return jsonify({'message': 'Password must be exactly 4 digits'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already taken'}), 400

    user = User(
        name=data.get('name', username),
        username=username,
        email=email,
        phone=data.get('phone', ''),
        password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role='customer',
        country=data.get('country', 'Kenya'),
        preferred_currency=data.get('preferred_currency', 'KES'),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'status': 'success',
        'message': 'Registration successful',
        'token': token,
        'access_token': token,
        'user': {
            'id': str(user.id),
            '_id': str(user.id),
            'name': user.name or user.username,
            'username': user.username,
            'email': user.email,
            'phone': user.phone or '',
            'country': user.country,
            'preferred_currency': user.preferred_currency,
            'role': user.role,
        }
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400

    if not is_valid_customer_password(data['password']):
        return jsonify({'message': 'Password must be exactly 4 digits'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': token,
        'access_token': token,
        'user': {
            'id': str(user.id),
            '_id': str(user.id),
            'name': user.name or user.username,
            'username': user.username or user.name,
            'email': user.email,
            'phone': user.phone or '',
            'country': user.country,
            'preferred_currency': user.preferred_currency,
            'role': user.role,
        }
    })

@app.route('/auth/google', methods=['GET', 'POST'])
def customer_google_login():
    if request.method == 'GET':
        return jsonify({
            'status': 'ready',
            'message': 'Customer Google sign-in is enabled. Send a POST request with a credential token.',
            'allowed_client_ids': get_google_client_ids(),
        })

    data = request.get_json(silent=True) or {}
    credential = data.get('credential') or data.get('id_token') or data.get('token')

    try:
        profile = verify_google_credential(credential)
        user, created = get_or_create_google_customer_user(profile)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

    return build_customer_auth_response(user, 201 if created else 200)

@app.route('/admin/auth/google', methods=['POST'])
def admin_google_login():
    data = request.get_json(silent=True) or {}
    credential = data.get('credential') or data.get('id_token') or data.get('token')

    try:
        profile = verify_google_credential(credential)
        user = get_or_create_google_admin_user(profile)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'message': str(exc)}), 403

    return build_admin_auth_response(user)

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def auth_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify({
        'status': 'success',
        'user': {
            '_id': str(user.id),
            'id': str(user.id),
            'name': user.name or user.username,
            'username': user.username or user.name,
            'email': user.email,
            'phone': user.phone or '',
            'country': user.country,
            'preferred_currency': user.preferred_currency,
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        }
    })

@app.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = int(get_jwt_identity())
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    cart_payload = [build_cart_item_payload(item) for item in cart_items]
    total_usd = sum(item['item_total'] for item in cart_payload)
    total_kes = sum(item['item_total_kes'] for item in cart_payload)
    
    return jsonify({
        'status': 'success',
        'cart': cart_payload,
        'total': {'usd': round(total_usd, 2), 'kes': round(total_kes, 2)}
    })

@app.route('/cart/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    quantity = int(data.get('quantity', 1))
    if not data.get('product_id') or quantity < 1:
        return jsonify({'error': 'Valid product_id and quantity are required'}), 400

    product = Product.query.get_or_404(data['product_id'])
    
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=data['product_id']).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=data['product_id'], quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Product added to cart'})

@app.route('/cart/update/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    quantity = int(data.get('quantity', 1) or 1)

    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not item:
        return jsonify({'error': 'Product not in cart'}), 404

    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity

    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Cart updated'})

@app.route('/cart/remove/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if not item:
        return jsonify({'error': 'Product not in cart'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Product removed from cart'})

@app.route('/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    user_id = int(get_jwt_identity())
    clear_user_cart_items(user_id)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Cart cleared'})

@app.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    user = User.query.get(user_id)
    
    try:
        order_items = resolve_order_items_for_checkout(user_id, data)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    shipping_kes = resolve_shipping_kes(data)

    try:
        promo_summary = resolve_promotion_for_checkout(user, data, order_items, shipping_kes)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    total_usd = round(float(promo_summary.get('final_total_kes', 0) or 0) / 128.5, 2)

    payment_method = data.get('payment_method', 'card')
    order = Order(
        order_id=str(uuid.uuid4())[:8].upper(),
        user_id=user_id,
        items=order_items,
        total_usd=total_usd,
        shipping_address=data.get('shipping_address', {}),
        payment_method=payment_method,
        payment_status='pending',
        order_status='processing',
        promo_code_id=promo_summary.get('promo_code_id'),
        promo_code=promo_summary.get('promo_code'),
        discount_type=promo_summary.get('discount_type'),
        discount_amount=float(promo_summary.get('discount_amount', 0) or 0),
        shipping_discount=float(promo_summary.get('shipping_discount', 0) or 0),
        final_total_after_discount=float(promo_summary.get('final_total_kes', 0) or 0),
    )

    db.session.add(order)
    db.session.flush()
    set_order_payment_state(
        order,
        **build_order_summary_payload(data, user, order_items, total_usd, promo_summary),
    )
    append_order_event(
        order,
        event_type='order_created',
        category='order',
        message=f"Order created with {len(order_items)} item(s) totaling KSh {float(promo_summary.get('final_total_kes', 0) or 0):,.0f}.",
        metadata={
            'payment_method': payment_method,
            'item_count': len(order_items),
        },
    )

    if payment_method == 'mpesa':
        grand_total_kes = float(promo_summary.get('final_total_kes', 0) or 0)
        payment_details = data.get('payment_details') or {}
        phone_number = payment_details.get('phone_number')

        if grand_total_kes <= 0:
            db.session.rollback()
            return jsonify({'message': 'A valid KES total is required for M-Pesa checkout'}), 400

        if not phone_number:
            db.session.rollback()
            return jsonify({'message': 'An M-Pesa phone number is required'}), 400

        try:
            stk_response, normalized_phone = start_mpesa_stk_push(
                phone_number=phone_number,
                amount_kes=grand_total_kes,
                order=order,
                description=f"Queen Koba order {order.order_id}",
            )
        except ValueError as error:
            db.session.rollback()
            return jsonify({'message': str(error)}), 400
        except requests.RequestException as error:
            db.session.rollback()
            response_text = error.response.text if error.response is not None else 'Unable to reach Safaricom'
            return jsonify({
                'message': 'Failed to initiate M-Pesa STK push',
                'details': response_text,
            }), 502

        set_order_payment_state(
            order,
            provider='mpesa',
            phone_number=normalized_phone,
            amount_kes=int(round(grand_total_kes)),
            merchant_request_id=stk_response.get('MerchantRequestID'),
            checkout_request_id=stk_response.get('CheckoutRequestID'),
            customer_message=stk_response.get('CustomerMessage'),
            response_code=stk_response.get('ResponseCode'),
            response_description=stk_response.get('ResponseDescription'),
            result_code=None,
            result_desc=None,
        )
        append_order_event(
            order,
            event_type='mpesa_stk_initiated',
            category='payment',
            message=f"M-Pesa STK push initiated to {normalized_phone}.",
            metadata={
                'phone_number': normalized_phone,
                'amount_kes': int(round(grand_total_kes)),
                'checkout_request_id': stk_response.get('CheckoutRequestID'),
            },
        )
        order.payment_status = 'initiated'
        order.order_status = 'processing'
        db.session.commit()

        return jsonify({
            'status': 'success',
            'order_id': order.order_id,
            'total': total_usd,
            'payment': {
                'provider': 'mpesa',
                'status': order.payment_status,
                'customer_message': stk_response.get('CustomerMessage'),
                'checkout_request_id': stk_response.get('CheckoutRequestID'),
                'merchant_request_id': stk_response.get('MerchantRequestID'),
            }
        })

    clear_user_cart_items(user_id)
    record_promotion_usage_for_order(order)
    append_order_event(
        order,
        event_type='payment_recorded',
        category='payment',
        message=f"Order recorded with {payment_method} payment method.",
        metadata={'payment_method': payment_method, 'payment_status': order.payment_status},
    )
    db.session.commit()

    return jsonify({
        'status': 'success',
        'order_id': order.order_id,
        'total': total_usd,
        'promo': promo_summary,
    })

@app.route('/payments/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json(silent=True) or {}
    callback = (
        data.get('Body', {})
        .get('stkCallback', {})
    )
    checkout_request_id = callback.get('CheckoutRequestID')
    order = find_order_by_checkout_request_id(checkout_request_id)

    if order:
        result_code = callback.get('ResultCode')
        result_desc = callback.get('ResultDesc')
        metadata = extract_mpesa_callback_metadata(callback.get('CallbackMetadata', {}))

        set_order_payment_state(
            order,
            result_code=result_code,
            result_desc=result_desc,
            receipt_number=metadata.get('MpesaReceiptNumber'),
            transaction_date=metadata.get('TransactionDate'),
            amount_kes=metadata.get('Amount') or get_order_payment_state(order).get('amount_kes'),
            phone_number=metadata.get('PhoneNumber') or get_order_payment_state(order).get('phone_number'),
            callback_payload=data,
        )
        order.payment_status = 'paid' if result_code == 0 else 'failed'
        order.order_status = 'processing' if result_code == 0 else 'payment_failed'
        append_order_event(
            order,
            event_type='mpesa_callback_received',
            category='payment',
            message='M-Pesa callback confirmed payment.' if result_code == 0 else f"M-Pesa callback reported failure: {result_desc}",
            metadata={
                'result_code': result_code,
                'result_desc': result_desc,
                'receipt_number': metadata.get('MpesaReceiptNumber'),
            },
        )
        if result_code == 0:
            clear_user_cart_items(order.user_id)
            record_promotion_usage_for_order(order)
        db.session.commit()

    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

@app.route('/payments/mpesa/status/<string:order_ref>', methods=['GET'])
@jwt_required()
def mpesa_status(order_ref):
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(order_id=order_ref, user_id=user_id).first()
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    if order.payment_method != 'mpesa':
        return jsonify({'message': 'Order is not an M-Pesa payment'}), 400

    if order.payment_status in ['paid', 'failed']:
        return jsonify({'status': 'success', 'payment': build_mpesa_status_response(order)})

    state = get_order_payment_state(order)
    checkout_request_id = state.get('checkout_request_id')
    if not checkout_request_id:
        return jsonify({'status': 'success', 'payment': build_mpesa_status_response(order)})

    try:
        query_response = query_mpesa_stk_status(checkout_request_id)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400
    except requests.RequestException as error:
        response_text = error.response.text if error.response is not None else 'Unable to reach Safaricom'
        set_order_payment_state(
            order,
            query_error=response_text,
        )
        append_order_event(
            order,
            event_type='mpesa_status_query_delayed',
            category='payment',
            message='M-Pesa status query is temporarily unavailable. Waiting for callback or next poll.',
            metadata={'details': response_text},
        )
        db.session.commit()
        return jsonify({
            'status': 'success',
            'payment': build_mpesa_status_response(order),
        })

    result_code_raw = query_response.get('ResultCode')
    result_code = int(result_code_raw) if str(result_code_raw).isdigit() else result_code_raw
    result_desc = query_response.get('ResultDesc')
    if result_code == 0:
        order.payment_status = 'paid'
        order.order_status = 'processing'
        clear_user_cart_items(user_id)
        record_promotion_usage_for_order(order)
    elif result_code in [1032, 1037, 2001, 1]:
        order.payment_status = 'failed'
        order.order_status = 'payment_failed'

    set_order_payment_state(
        order,
        result_code=result_code,
        result_desc=result_desc,
        query_payload=query_response,
        query_error=None,
    )
    if result_code == 0:
        append_order_event(
            order,
            event_type='mpesa_status_confirmed',
            category='payment',
            message='M-Pesa payment confirmed from status query.',
            metadata={'result_code': result_code, 'result_desc': result_desc},
        )
    elif result_code in [1032, 1037, 2001, 1]:
        append_order_event(
            order,
            event_type='mpesa_status_failed',
            category='payment',
            message=f"M-Pesa status query reported failure: {result_desc}",
            metadata={'result_code': result_code, 'result_desc': result_desc},
        )
    db.session.commit()

    return jsonify({'status': 'success', 'payment': build_mpesa_status_response(order)})

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'orders': [build_admin_order_payload(o) for o in orders]
    })

@app.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify({
        'status': 'success',
        'order': build_admin_order_payload(order)
    })

@app.route('/admin/auth/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or user.role not in ['admin', 'super_admin']:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return build_admin_auth_response(user)

@app.route('/admin/dashboard/kpis', methods=['GET'])
@admin_required()
def get_dashboard_kpis():
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    def build_period_metrics(start_at, end_at):
        period_orders = Order.query.filter(
            Order.created_at >= start_at,
            Order.created_at < end_at,
        ).all()
        paid_period_orders = [
            order for order in period_orders
            if build_admin_order_payload(order).get('payment_status') == 'paid'
        ]
        revenue = sum(
            float(build_admin_order_payload(order).get('grand_total_kes', 0) or 0)
            for order in paid_period_orders
        )
        orders_count = len(period_orders)
        customers_count = User.query.filter(
            User.role == 'customer',
            User.created_at >= start_at,
            User.created_at < end_at,
        ).count()
        conversion_rate = round((len(paid_period_orders) / orders_count) * 100, 1) if orders_count else 0
        return {
            'revenue': revenue,
            'orders_count': orders_count,
            'customers_count': customers_count,
            'conversion_rate': conversion_rate,
        }

    def trend_percent(current, previous):
        current = float(current or 0)
        previous = float(previous or 0)
        if previous == 0:
            return 0 if current == 0 else 100
        return round(((current - previous) / previous) * 100, 1)

    current = build_period_metrics(thirty_days_ago, now)
    previous = build_period_metrics(sixty_days_ago, thirty_days_ago)

    return jsonify({
        'total_revenue': current['revenue'],
        'total_orders': current['orders_count'],
        'total_customers': User.query.filter_by(role='customer').count(),
        'conversion_rate': current['conversion_rate'],
        'low_stock_items': Product.query.filter_by(in_stock=False).count(),
        'expiring_soon': 0,
        'expiring_soon_tracked': False,
        'revenue_change': trend_percent(current['revenue'], previous['revenue']),
        'orders_change': trend_percent(current['orders_count'], previous['orders_count']),
        'customers_change': trend_percent(current['customers_count'], previous['customers_count']),
        'conversion_change': trend_percent(current['conversion_rate'], previous['conversion_rate']),
    })

@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required()
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
                ,
                'image_url': p.image_url,
                'discount_percentage': p.discount_percentage or 0,
                'on_sale': p.on_sale or False
            } for p in products]
        })
    else:
        data = request.get_json() or {}
        base_price_usd = data.get('base_price_usd')
        prices = data.get('prices') or {}
        if base_price_usd is None and isinstance(prices, dict):
            kes = prices.get('KES', {})
            kes_amount = kes.get('amount') if isinstance(kes, dict) else None
            if kes_amount:
                base_price_usd = round(float(kes_amount) / 128.5, 2)
        base_price_usd = float(base_price_usd or 0)

        product = Product(
            name=data.get('name'),
            description=data.get('description', ''),
            category=data.get('category', 'Other'),
            base_price_usd=base_price_usd,
            prices=prices if prices else calculate_prices(base_price_usd),
            in_stock=bool(data.get('in_stock', True)),
            image_url=data.get('image_url'),
            discount_percentage=float(data.get('discount_percentage', 0) or 0),
            on_sale=bool(data.get('on_sale', False)),
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'status': 'success', 'product': {'_id': str(product.id)}}), 201

@app.route('/admin/products/<int:product_id>', methods=['PUT', 'DELETE'])
@admin_required()
def admin_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        data = request.get_json() or {}
        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        if 'prices' in data and isinstance(data['prices'], dict):
            kes = data['prices'].get('KES', {})
            kes_amount = kes.get('amount') if isinstance(kes, dict) else None
            if kes_amount:
                product.base_price_usd = round(float(kes_amount) / 128.5, 2)

        if 'base_price_usd' in data and 'prices' not in data:
            product.prices = calculate_prices(float(product.base_price_usd))

        db.session.commit()
        return jsonify({'status': 'success'})

@app.route('/admin/orders', methods=['GET'])
@admin_required()
def admin_get_orders():
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    return jsonify({
        'orders': [build_admin_order_payload(o) for o in orders]
    })

@app.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
@admin_required()
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    new_status = data.get('status')

    if not new_status:
        return jsonify({'error': 'Status is required'}), 400

    order.order_status = new_status
    if data.get('note'):
        set_order_payment_state(order, note=data.get('note'))
    append_order_event(
        order,
        event_type='admin_status_updated',
        category='order',
        actor='admin',
        message=f"Order status changed to {new_status}.",
        metadata={'status': new_status, 'note': data.get('note')},
    )
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Order status updated'})

@app.route('/admin/customers', methods=['GET'])
@admin_required()
def admin_get_customers():
    customers = User.query.filter_by(role='customer').limit(50).all()

    payload = []
    for customer in customers:
        customer_orders = Order.query.filter_by(user_id=customer.id).order_by(Order.created_at.desc()).all()
        order_payloads = [build_admin_order_payload(order) for order in customer_orders]
        total_spent_kes = sum(
            float(order.get('grand_total_kes', 0) or 0)
            for order in order_payloads
            if order.get('payment_status') == 'paid'
        )
        cart_items = CartItem.query.filter_by(user_id=customer.id).all()

        payload.append({
            '_id': str(customer.id),
            'name': customer.name or customer.username,
            'username': customer.username or customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'country': customer.country or 'Kenya',
            'preferred_currency': customer.preferred_currency or 'KES',
            'role': customer.role,
            'created_at': customer.created_at.isoformat(),
            'orders': order_payloads,
            'total_spent': total_spent_kes,
            'total_spent_kes': total_spent_kes,
            'cart': [{
                'product_id': item.product_id,
                'quantity': item.quantity,
            } for item in cart_items]
        })

    return jsonify({
        'customers': payload
    })

@app.route('/admin/profile/password', methods=['PUT'])
@admin_required()
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
@admin_required()
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
@admin_required()
def admin_approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = 'approved'
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/reviews/<int:review_id>/reject', methods=['PUT'])
@admin_required()
def admin_reject_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = 'rejected'
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/reviews/<int:review_id>', methods=['DELETE'])
@admin_required()
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
    promotions = [
        promo for promo in Promotion.query.filter_by(status='active').all()
        if promo_is_active(promo)
    ]
    return jsonify({
        'promotions': [build_promotion_payload(promo) for promo in promotions]
    })

@app.route('/promotions/validate', methods=['POST'])
def validate_promo_code():
    data = request.get_json() or {}
    code = normalize_promo_code(data.get('code'))
    if not code:
        return jsonify({'error': 'Promo code is required'}), 400

    user = get_optional_current_user()

    try:
        order_items = resolve_order_items_for_promo_request(user, data)
        shipping_kes = resolve_shipping_kes(data)
        promo = Promotion.query.filter_by(code=code).first()
        summary = evaluate_promotion(promo, user, order_items, shipping_kes)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    return jsonify({
        'status': 'success',
        'promo': summary,
    })

@app.route('/cart/apply-promocode', methods=['POST'])
def apply_cart_promo_code():
    data = request.get_json() or {}
    data['code'] = normalize_promo_code(data.get('code'))
    if not data.get('code'):
        return jsonify({'error': 'Promo code is required'}), 400

    user = get_optional_current_user()
    try:
        order_items = resolve_order_items_for_promo_request(user, data)
        shipping_kes = resolve_shipping_kes(data)
        promo = Promotion.query.filter_by(code=data['code']).first()
        summary = evaluate_promotion(promo, user, order_items, shipping_kes)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    return jsonify({
        'status': 'success',
        'promo': summary,
    })

@app.route('/cart/remove-promocode', methods=['DELETE'])
def remove_cart_promo_code():
    return jsonify({
        'status': 'success',
        'message': 'Promo code removed',
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
@admin_required()
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

@app.route('/admin/support-tickets/<int:ticket_id>', methods=['GET'])
@admin_required()
def admin_get_support_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    return jsonify({
        'ticket': {
            '_id': str(ticket.id),
            'customer_name': ticket.customer_name,
            'customer_email': ticket.customer_email,
            'subject': ticket.subject,
            'message': ticket.message,
            'priority': ticket.priority,
            'status': ticket.status,
            'replies': ticket.replies or [],
            'created_at': ticket.created_at.isoformat(),
        }
    })

@app.route('/admin/support-tickets/<int:ticket_id>/status', methods=['PUT'])
@admin_required()
def admin_update_support_ticket_status(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    data = request.get_json() or {}
    ticket.status = data.get('status', ticket.status)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/support-tickets/<int:ticket_id>/reply', methods=['POST'])
@admin_required()
def admin_reply_support_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    data = request.get_json() or {}
    replies = list(ticket.replies or [])
    replies.append({
        'message': data.get('message', ''),
        'created_at': datetime.utcnow().isoformat(),
        'admin': True
    })
    ticket.replies = replies
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/promotions', methods=['GET', 'POST'])
@admin_required()
def admin_promotions():
    if request.method == 'GET':
        promotions = Promotion.query.order_by(Promotion.created_at.desc()).all()
        search = str(request.args.get('search') or '').strip().lower()
        status_filter = str(request.args.get('status') or '').strip().lower()
        discount_type_filter = str(request.args.get('discount_type') or '').strip().lower()
        campaign_filter = str(request.args.get('campaign_type') or '').strip().lower()

        if search:
            promotions = [
                promo for promo in promotions
                if search in (promo.code or '').lower() or search in (promo.description or '').lower()
            ]
        if status_filter:
            promotions = [promo for promo in promotions if (promo.status or '').lower() == status_filter]
        if discount_type_filter:
            promotions = [promo for promo in promotions if (promo.type or '').lower() == discount_type_filter]
        if campaign_filter:
            promotions = [promo for promo in promotions if (promo.campaign_type or '').lower() == campaign_filter]

        return jsonify({
            'promotions': [build_promotion_payload(promo, include_stats=True) for promo in promotions]
        })
    
    data = request.get_json() or {}
    try:
        payload = validate_promotion_payload(data)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    existing = Promotion.query.filter_by(code=payload['code']).first()
    if existing:
        return jsonify({'error': 'A promo code with that code already exists'}), 409

    promo = Promotion()
    apply_promotion_model_updates(promo, payload, admin_user_id=int(get_jwt_identity()))
    db.session.add(promo)
    db.session.flush()
    sync_promotion_targets(promo, payload)
    db.session.commit()
    return jsonify({'status': 'success', 'promotion': build_promotion_payload(promo, include_stats=True)}), 201

@app.route('/admin/promotions/generate-random', methods=['POST'])
@admin_required()
def admin_generate_random_promotion_code():
    data = request.get_json() or {}
    prefix = data.get('prefix', 'QK')
    attempts = 0
    code = generate_random_promo_code(prefix=prefix, length=parse_int(data.get('length'), 8) or 8)
    while Promotion.query.filter_by(code=code).first():
        attempts += 1
        code = generate_random_promo_code(prefix=prefix, length=parse_int(data.get('length'), 8) or 8)
        if attempts > 5:
            break
    return jsonify({'status': 'success', 'code': code})

@app.route('/admin/promotions/<int:promo_id>/stats', methods=['GET'])
@admin_required()
def admin_get_promotion_stats(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    return jsonify({
        'status': 'success',
        'promotion': build_promotion_payload(promo, include_stats=True),
    })

@app.route('/admin/promotions/<int:promo_id>/duplicate', methods=['POST'])
@admin_required()
def admin_duplicate_promotion(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    duplicated = Promotion()
    duplicated_payload = build_promotion_payload(promo)
    payload = validate_promotion_payload({
        **duplicated_payload,
        'code': generate_random_promo_code(prefix=promo.code[:4] or 'QK', length=8),
        'status': 'inactive',
        'is_active': False,
        'product_ids': duplicated_payload.get('product_ids', []),
        'categories': duplicated_payload.get('categories', []),
        'user_ids': duplicated_payload.get('user_ids', []),
    })
    apply_promotion_model_updates(duplicated, payload, admin_user_id=int(get_jwt_identity()))
    db.session.add(duplicated)
    db.session.flush()
    sync_promotion_targets(duplicated, payload)
    db.session.commit()
    return jsonify({
        'status': 'success',
        'promotion': build_promotion_payload(duplicated, include_stats=True),
    }), 201

@app.route('/admin/promotions/<int:promo_id>/toggle', methods=['PATCH'])
@admin_required()
def admin_toggle_promotion_status(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    promo.status = 'inactive' if promo.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'status': 'success', 'promotion': build_promotion_payload(promo, include_stats=True)})

@app.route('/admin/promotions/<int:promo_id>/status', methods=['PUT'])
@admin_required()
def admin_update_promotion_status(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    data = request.get_json() or {}
    next_status = str(data.get('status') or promo.status).strip().lower()
    if next_status not in ['active', 'inactive']:
        return jsonify({'error': 'Status must be active or inactive'}), 400
    promo.status = next_status
    db.session.commit()
    return jsonify({'status': 'success', 'promotion': build_promotion_payload(promo, include_stats=True)})

@app.route('/admin/promotions/<int:promo_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required()
def admin_promotion_detail(promo_id):
    promo = Promotion.query.get_or_404(promo_id)
    if request.method == 'GET':
        return jsonify({'promotion': build_promotion_payload(promo, include_stats=True)})

    if request.method == 'DELETE':
        if promo.uses or PromotionUsage.query.filter_by(promo_code_id=promo.id).count() > 0 or Order.query.filter_by(promo_code_id=promo.id).count() > 0:
            promo.status = 'inactive'
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Promo code has existing usage history and was deactivated instead of deleted',
                'promotion': build_promotion_payload(promo, include_stats=True),
            })

        PromotionProduct.query.filter_by(promo_code_id=promo.id).delete()
        PromotionCategory.query.filter_by(promo_code_id=promo.id).delete()
        PromotionUser.query.filter_by(promo_code_id=promo.id).delete()
        db.session.delete(promo)
        db.session.commit()
        return jsonify({'status': 'success'})

    data = request.get_json() or {}
    try:
        payload = validate_promotion_payload(data)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    existing = Promotion.query.filter_by(code=payload['code']).first()
    if existing and existing.id != promo.id:
        return jsonify({'error': 'A promo code with that code already exists'}), 409

    apply_promotion_model_updates(promo, payload, admin_user_id=int(get_jwt_identity()))
    sync_promotion_targets(promo, payload)
    db.session.commit()
    return jsonify({'status': 'success', 'promotion': build_promotion_payload(promo, include_stats=True)})

@app.route('/admin/payments', methods=['GET'])
@admin_required()
def admin_get_payments():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    payments = []
    for order in orders:
        payload = build_admin_order_payload(order)
        payments.append({
            '_id': payload['_id'],
            'order_id': payload['order_id'],
            'customer_name': payload['customer_name'],
            'customer_email': payload['customer_email'],
            'customer_phone': payload['customer_phone'],
            'amount': payload['grand_total_kes'],
            'amount_kes': payload['grand_total_kes'],
            'subtotal_kes': payload['subtotal_kes'],
            'shipping_kes': payload['shipping_kes'],
            'discount_percent': payload['discount_percent'],
            'payment_method': payload['payment_method'],
            'payment_status': payload['payment_status'],
            'order_status': payload['order_status'],
            'payment_receipt': payload['payment_receipt'],
            'payment_details': payload['payment_details'],
            'events': payload['events'],
            'last_event': payload['last_event'],
            'created_at': payload['created_at'],
            'updated_at': payload['updated_at'],
        })
    return jsonify({'payments': payments})

@app.route('/admin/shipping-zones', methods=['GET', 'POST'])
@admin_required()
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
@admin_required()
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

@app.route('/admin/shipping-zones/<int:zone_id>/status', methods=['PUT'])
@admin_required()
def admin_shipping_zone_status(zone_id):
    zone = ShippingZone.query.get_or_404(zone_id)
    data = request.get_json() or {}
    zone.active = bool(data.get('active', zone.active))
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/content', methods=['GET', 'PUT'])
@admin_required()
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

@app.route('/content', methods=['GET'])
def public_content():
    all_content = SiteContent.query.all()
    return jsonify({'content': {c.key: c.value for c in all_content}})

@app.route('/admin/admins', methods=['GET'])
@admin_required()
def admin_get_admins():
    admins = User.query.filter(User.role.in_(['admin', 'super_admin'])).all()
    return jsonify({
        'admins': [{
            '_id': str(a.id),
            'email': a.email,
            'full_name': a.username or a.name or 'Admin',
            'role': a.role,
            'permissions': a.permissions or ['*'],
            'status': a.status or 'active',
            'created_at': a.created_at.isoformat() if a.created_at else None,
        } for a in admins]
    })

@app.route('/admin/admins', methods=['POST'])
@admin_required()
def admin_create_admin():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    admin = User(
        name=data.get('full_name'),
        username=data.get('full_name'),
        email=email,
        password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role=data.get('role', 'admin'),
        permissions=data.get('permissions', ['read', 'write']),
        status='active',
    )
    db.session.add(admin)
    db.session.commit()
    return jsonify({'status': 'success', 'admin': {'_id': str(admin.id)}}), 201

@app.route('/admin/admins/<int:admin_id>', methods=['PUT'])
@admin_required()
def admin_update_admin(admin_id):
    admin = User.query.get_or_404(admin_id)
    data = request.get_json() or {}

    if 'full_name' in data:
        admin.name = data['full_name']
        admin.username = data['full_name']
    if 'email' in data:
        admin.email = data['email']
    if 'role' in data:
        admin.role = data['role']
    if 'permissions' in data:
        admin.permissions = data['permissions']
    if data.get('password'):
        admin.password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/admins/<int:admin_id>/status', methods=['PUT'])
@admin_required()
def admin_update_admin_status(admin_id):
    admin = User.query.get_or_404(admin_id)
    data = request.get_json() or {}
    admin.status = data.get('status', admin.status)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/admins/<int:admin_id>', methods=['DELETE'])
@admin_required()
def admin_delete_admin(admin_id):
    admin = User.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()

    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"

    print("\n" + "="*70)
    print("   🚀 QUEEN KOBA SKINCARE API - POSTGRESQL EDITION")
    print("="*70)
    print(f"✅ Database connected ({app.config['SQLALCHEMY_DATABASE_URI']})")
    print(f"🌐 Server: http://0.0.0.0:{port}")
    print("🔑 Admin: admin@queenkoba.com / admin123")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=debug)
