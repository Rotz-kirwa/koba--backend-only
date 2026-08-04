# app/routes/payments.py
from flask import Blueprint, jsonify, request
from app.models import PaymentMethod, User
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Payment methods configuration for East Africa[citation:4][citation:7]
EAST_AFRICA_PAYMENT_METHODS = [
    {
        'name': 'M-Pesa',
        'code': 'mpesa',
        'countries': ['Kenya', 'Tanzania'],
        'description': 'Mobile money transfer service',
        'icon_url': '/icons/mpesa.png'
    },
    {
        'name': 'Airtel Money',
        'code': 'airtel_money',
        'countries': ['Kenya', 'Uganda', 'Tanzania', 'Rwanda'],
        'description': 'Mobile money service by Airtel',
        'icon_url': '/icons/airtel.png'
    },
    {
        'name': 'MTN Mobile Money',
        'code': 'mtn_momo',
        'countries': ['Uganda', 'Rwanda', 'DRC Congo'],
        'description': 'MTN mobile money service',
        'icon_url': '/icons/mtn.png'
    },
    {
        'name': 'Tigo Pesa',
        'code': 'tigo_pesa',
        'countries': ['Tanzania'],
        'description': 'Tigo mobile money service',
        'icon_url': '/icons/tigo.png'
    },
    {
        'name': 'Visa/Mastercard',
        'code': 'card',
        'countries': ['Kenya', 'Uganda', 'Tanzania', 'Rwanda', 'Burundi', 'DRC Congo'],
        'description': 'Credit/Debit card payments',
        'icon_url': '/icons/card.png'
    },
    {
        'name': 'Bank Transfer',
        'code': 'bank_transfer',
        'countries': ['Kenya', 'Uganda', 'Tanzania', 'Rwanda', 'Burundi', 'DRC Congo'],
        'description': 'Direct bank transfer',
        'icon_url': '/icons/bank.png'
    },
    {
        'name': 'PayPal',
        'code': 'paypal',
        'countries': ['Kenya', 'Uganda', 'Tanzania', 'Rwanda'],
        'description': 'International online payments',
        'icon_url': '/icons/paypal.png'
    },
    {
        'name': 'Contactless/Tap-to-Pay',
        'code': 'contactless',
        'countries': ['Kenya', 'Uganda', 'Rwanda'],  # Growing in adoption[citation:7]
        'description': 'NFC contactless payments',
        'icon_url': '/icons/contactless.png'
    }
]

@payments_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """Get all available payment methods"""
    country = request.args.get('country', 'Kenya')
    
    # Filter methods by country
    methods = []
    for method in EAST_AFRICA_PAYMENT_METHODS:
        if country in method['countries']:
            methods.append(method)
    
    return jsonify({
        'status': 'success',
        'country': country,
        'methods': methods,
        'count': len(methods)
    })

@payments_bp.route('/user-methods', methods=['GET'])
@jwt_required()
def get_user_payment_methods():
    """Get payment methods for logged in user's country"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    methods = []
    for method in EAST_AFRICA_PAYMENT_METHODS:
        if user.country in method['countries']:
            methods.append(method)
    
    return jsonify({
        'status': 'success',
        'user_country': user.country,
        'preferred_currency': user.preferred_currency,
        'methods': methods
    })

@payments_bp.route('/initialize', methods=['POST'])
@jwt_required()
def initialize_payment():
    """Initialize a payment transaction"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    required_fields = ['amount', 'currency', 'payment_method', 'product_ids']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    user = User.query.get(user_id)
    
    # Check if payment method is available in user's country
    method_available = False
    for method in EAST_AFRICA_PAYMENT_METHODS:
        if method['code'] == data['payment_method'] and user.country in method['countries']:
            method_available = True
            break
    
    if not method_available:
        return jsonify({
            'status': 'error',
            'message': f"Payment method not available in {user.country}"
        }), 400
    
    # Generate payment reference
    import uuid
    payment_reference = str(uuid.uuid4())[:8].upper()
    
    # Store payment in database (simplified)
    # In real implementation, you'd create a PaymentTransaction model
    
    return jsonify({
        'status': 'success',
        'message': 'Payment initialized',
        'payment_reference': payment_reference,
        'amount': data['amount'],
        'currency': data['currency'],
        'payment_method': data['payment_method'],
        'next_steps': 'Redirect user to payment gateway or show payment instructions'
    })