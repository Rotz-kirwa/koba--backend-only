from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import CartItem, Product
from ..utils.helpers import build_cart_item_payload, clear_user_cart_items

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('', methods=['GET'])
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

@cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if not product_id or quantity < 1:
        return jsonify({'error': 'Valid product_id and quantity are required'}), 400

    product = Product.query.get_or_404(product_id)
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Product added to cart'})

@cart_bp.route('/update/<int:product_id>', methods=['PUT'])
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

@cart_bp.route('/remove/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if not item:
        return jsonify({'error': 'Product not in cart'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Product removed from cart'})

@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    user_id = int(get_jwt_identity())
    clear_user_cart_items(user_id)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Cart cleared'})
