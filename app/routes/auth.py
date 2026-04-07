import bcrypt
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..extensions import db
from ..models import User
from ..utils.google_auth import verify_google_credential, get_google_client_ids

auth_bp = Blueprint('auth', __name__)

def build_customer_auth_response(user, status_code=200):
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'status': 'success',
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
    }), status_code

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username') or data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Username, email and password required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

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

    return build_customer_auth_response(user, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    return build_customer_auth_response(user)

@auth_bp.route('/google', methods=['GET', 'POST'])
def customer_google_login():
    if request.method == 'GET':
        return jsonify({
            'status': 'ready',
            'message': 'Google sign-in is enabled.',
            'allowed_client_ids': get_google_client_ids(),
        })

    data = request.get_json(silent=True) or {}
    credential = data.get('credential') or data.get('id_token') or data.get('token')

    try:
        profile = verify_google_credential(credential)
        email = profile['email']
        user = User.query.filter_by(email=email).first()
        created = False
        if not user:
            user = User(
                email=email,
                name=profile.get('name'),
                username=profile.get('sub'),
                role='customer',
                is_guest=False
            )
            db.session.add(user)
            db.session.commit()
            created = True
        
        return build_customer_auth_response(user, 201 if created else 200)
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def auth_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify({
        'status': 'success',
        'user': {
            'id': str(user.id),
            'name': user.name or user.username,
            'email': user.email,
            'role': user.role,
        }
    })
