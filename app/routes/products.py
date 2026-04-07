from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Product, User, Order, SiteContent
from ..utils.helpers import (
    parse_bool, parse_int, build_public_product_payload
)

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def get_products():
    lite = parse_bool(request.args.get('lite'))
    limit = parse_int(request.args.get('limit'))
    products_query = Product.query.order_by(Product.id.asc())
    if limit and limit > 0:
        products_query = products_query.limit(limit)
    products = products_query.all()
    return jsonify({
        'status': 'success',
        'lite': lite,
        'count': len(products),
        'products': [build_public_product_payload(p, lite=lite) for p in products]
    })

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'status': 'success',
        'product': build_public_product_payload(product, lite=False)
    })

@products_bp.route('/content', methods=['GET'])
def public_content():
    all_content = SiteContent.query.all()
    lite = parse_bool(request.args.get('lite'))
    content = {
        'hero_title': 'Dark Spots & Uneven Tone Stealing Your Glow?',
        'hero_subtitle': 'Naturally brighten with toxin-free, melanin-safe luxury skincare.',
        'about_title': 'Explore The Full Ritual',
        'about_description': 'Explore our complete skincare lineup, mask, toner, serum, cream, and cleanser.',
        'contact_email': 'info@queenkoba.com',
        'contact_phone': '0119 559 180',
        'instagram_handle': '@queenkoba',
    }
    content.update({c.key: c.value for c in all_content})
    if lite:
        content = {k: v for k, v in content.items() if k.startswith(('contact_', 'instagram_'))}
    return jsonify(content)

@products_bp.route('/payment-methods/<country>', methods=['GET'])
def get_payment_methods(country):
    methods_map = {
        'Kenya': [
            {'name': 'M-Pesa', 'code': 'mpesa'},
            {'name': 'Card / Google Pay', 'code': 'card'}
        ],
        'Other': [
            {'name': 'Card / Google Pay', 'code': 'card'}
        ]
    }
    return jsonify(methods_map.get(country, methods_map['Other']))

@products_bp.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'counts': {
                'products': Product.query.count(),
                'users': User.query.count(),
                'orders': Order.query.count()
            }
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
