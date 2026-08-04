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
