from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import mongo
import bcrypt
from datetime import datetime
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if mongo.db.users.find_one({'email': data.get('email')}):
        return jsonify({'error': 'Email exists'}), 400
    
    user = {
        '_id': str(uuid.uuid4()),
        'email': data['email'],
        'password_hash': bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode(),
        'country': data.get('country', 'Kenya'),
        'created_at': datetime.utcnow()
    }
    
    mongo.db.users.insert_one(user)
    
    token = create_access_token(identity=user['_id'])
    user.pop('password_hash')
    
    return jsonify({
        'status': 'success',
        'token': token,
        'user': user
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = mongo.db.users.find_one({'email': data.get('email')})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(data['password'].encode(), user['password_hash'].encode()):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_access_token(identity=str(user['_id']))
    user.pop('password_hash')
    user['_id'] = str(user['_id'])
    
    return jsonify({
        'status': 'success',
        'token': token,
        'user': user
    })
