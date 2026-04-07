from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, create_access_token
from ..extensions import db
from ..models import Order, User, Review
from ..utils.helpers import (
    build_admin_order_payload, 
    set_order_payment_state, 
    append_order_event,
    parse_int,
    normalize_delivery_text,
    normalize_delivery_zone
)
from ..utils.google_auth import (
    verify_google_credential, 
    get_google_allowed_admin_emails
)

admin_bp = Blueprint('admin', __name__)

def admin_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id)) if user_id else None

            if not user or user.role not in ['admin', 'super_admin'] or user.status != 'active':
                return jsonify({'error': 'Admin access required'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def build_admin_auth_response(user):
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'status': 'success',
        'token': token,
        'access_token': token,
        'user': {
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'role': user.role,
        }
    })

@admin_bp.route('/auth/google', methods=['POST'])
def admin_google_login():
    data = request.get_json(silent=True) or {}
    credential = data.get('credential') or data.get('id_token') or data.get('token')

    try:
        profile = verify_google_credential(credential)
        email = profile['email']
        allowed_emails = get_google_allowed_admin_emails()
        
        if allowed_emails and email not in allowed_emails:
            return jsonify({'message': 'Email not authorized for admin access'}), 403
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'Admin account not found'}), 404
            
        if user.role not in ['admin', 'super_admin']:
            return jsonify({'message': 'Insufficient permissions'}), 403
            
        return build_admin_auth_response(user)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

@admin_bp.route('/orders', methods=['GET'])
@admin_required()
def admin_get_orders():
    search = normalize_delivery_text(request.args.get('search'))
    limit = parse_int(request.args.get('limit'), 100) or 100
    
    orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
    payloads = [build_admin_order_payload(o) for o in orders]
    
    # Filter logic can be expanded here as seen in monolith
    return jsonify({
        'orders': payloads,
        'count': len(payloads),
    })

@admin_bp.route('/orders/<int:order_id>', methods=['GET'])
@admin_required()
def admin_get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'order': build_admin_order_payload(order)
    })

@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
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
        event_type='status_update',
        message=f"Order status updated to {new_status}"
    )
    
    db.session.commit()
    return jsonify({'status': 'success'})

@admin_bp.route('/reviews', methods=['GET'])
@admin_required()
def admin_get_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return jsonify({
        'reviews': [{
            'id': r.id,
            'product_id': r.product_id,
            'product_name': r.product_name,
            'customer_name': r.customer_name,
            'rating': r.rating,
            'comment': r.comment,
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reviews]
    })
