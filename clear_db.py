from flask import Flask, jsonify
from flask_pymongo import PyMongo
import bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/queenkoba')
mongo = PyMongo(app)

@app.route('/clear-all-data', methods=['POST'])
def clear_all_data():
    try:
        # Clear all collections
        collections = [
            'products', 'orders', 'users', 'promotions', 
            'reviews', 'shipping_zones', 'site_content', 'support_tickets'
        ]
        
        results = {}
        for collection in collections:
            count = mongo.db[collection].count_documents({})
            mongo.db[collection].delete_many({})
            results[collection] = f"Cleared {count} documents"
        
        # Create super admin
        admin = {
            'username': 'Queen Koba Admin',
            'email': 'admin@queenkoba.com',
            'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(),
            'role': 'super_admin',
            'permissions': ['*'],
            'status': 'active',
            'created_at': datetime.utcnow()
        }
        mongo.db.users.insert_one(admin)
        
        return jsonify({
            'status': 'success',
            'message': 'All data cleared and super admin created',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001)
