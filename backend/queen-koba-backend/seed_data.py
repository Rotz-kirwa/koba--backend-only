from flask import Flask
from flask_pymongo import PyMongo
from datetime import datetime
import uuid
import bcrypt

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/queenkoba'
mongo = PyMongo(app)

with app.app_context():
    # Clear old data
    mongo.db.products.drop()
    mongo.db.users.drop()
    
    # Products with multi-currency prices
    products = [
        {
            'name': 'Complex Clarifier Cream',
            'description': 'Luxurious clarifying cream',
            'base_price_usd': 29.99,
            'category': 'Cream',
            'prices': [
                {'currency': 'KES', 'price': 3850, 'country': 'Kenya'},
                {'currency': 'UGX', 'price': 107400, 'country': 'Uganda'},
                {'currency': 'BIF', 'price': 85400, 'country': 'Burundi'},
                {'currency': 'CDF', 'price': 80970, 'country': 'DRC Congo'}
            ]
        },
        {
            'name': 'Complexion Clarifier Serum',
            'description': 'Vitamin C serum',
            'base_price_usd': 34.50,
            'category': 'Serum',
            'prices': [
                {'currency': 'KES', 'price': 4430, 'country': 'Kenya'},
                {'currency': 'UGX', 'price': 123500, 'country': 'Uganda'},
                {'currency': 'BIF', 'price': 98300, 'country': 'Burundi'},
                {'currency': 'CDF', 'price': 93150, 'country': 'DRC Congo'}
            ]
        },
        {
            'name': 'Complexion Clarifying Mask',
            'description': 'Detoxifying clay mask',
            'base_price_usd': 25.75,
            'category': 'Mask',
            'prices': [
                {'currency': 'KES', 'price': 3308, 'country': 'Kenya'},
                {'currency': 'UGX', 'price': 92200, 'country': 'Uganda'},
                {'currency': 'BIF', 'price': 73400, 'country': 'Burundi'},
                {'currency': 'CDF', 'price': 69525, 'country': 'DRC Congo'}
            ]

        },
        {
         "name": "Complexion Clarifying Cleanser",
         "description": "Gentle foaming cleanser",
         "category": "Cleanser",
         "in_stock": True,
            "prices": [
                {"currency": "KES", "price": 2900, "country": "Kenya"},
                {"currency": "UGX", "price": 81000, "country": "Uganda"},
                {"currency": "BIF", "price": 64500, "country": "Burundi"},
                {"currency": "CDF", "price": 61000, "country": "DRC Congo"}
            ]
        },
        {
            "name": "Complexion Clarifying Toner",
            "description": "Balancing toner for all skin types",
            "category": "Toner",
            "in_stock": True,
            "prices": [
                {"currency": "KES", "price": 3150, "country": "Kenya"},
                {"currency": "UGX", "price": 88000, "country": "Uganda"},
                {"currency": "BIF", "price": 70000, "country": "Burundi"},
                {"currency": "CDF", "price": 66500, "country": "DRC Congo"}
            ]
        }
        
    ]
    
    for p in products:
        p['_id'] = str(uuid.uuid4())
        p['created_at'] = datetime.utcnow()
        p['in_stock'] = True
        mongo.db.products.insert_one(p)
        print(f"Added: {p['name']}")
    
    # Admin user
    admin = {
        '_id': str(uuid.uuid4()),
        'email': 'admin@queenkoba.com',
        'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(),
        'country': 'Kenya',
        'created_at': datetime.utcnow(),
        'role': 'admin'
    }
    mongo.db.users.insert_one(admin)
    
    print(f"\n✅ Added {len(products)} products")
    print("👤 Admin: admin@queenkoba.com / admin123")
    print("\n📊 Sample prices for Cream (KES 3850, UGX 107400, etc.)")
