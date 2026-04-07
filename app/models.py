from datetime import datetime
from .extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    is_guest = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100))
    username = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=True)
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

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    provider = db.Column(db.String(50), default='mpesa', nullable=False)
    provider_reference = db.Column(db.String(100), unique=True, nullable=False, index=True)
    merchant_request_id = db.Column(db.String(100), nullable=True, index=True)
    receipt_number = db.Column(db.String(100), unique=True, nullable=True, index=True)
    account_reference = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='initiated', nullable=False)
    result_code = db.Column(db.String(20), nullable=True)
    result_desc = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    raw_response = db.Column(db.JSON)
    callback_payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = db.relationship('Order', backref=db.backref('payment_transactions', lazy=True))

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