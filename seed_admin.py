#!/usr/bin/env python3
from pymongo import MongoClient
import bcrypt
from datetime import datetime
from bson import ObjectId

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['queenkoba']

# Check if admin exists
existing_admin = db.users.find_one({'email': 'admin@queenkoba.com'})

if existing_admin:
    print("❌ Admin user already exists!")
    print(f"Email: admin@queenkoba.com")
    print("If you need to reset, delete the user first.")
else:
    # Create super admin user
    admin = {
        '_id': str(uuid.uuid4()),
        'username': 'Queen Koba Admin',
        'email': 'admin@queenkoba.com',
        'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(),
        'role': 'super_admin',
        'permissions': ['*'],
        'status': 'active',
        'created_at': datetime.utcnow()
    }
    
    db.users.insert_one(admin)
    print("✅ Super Admin user created successfully!")
    print(f"Email: admin@queenkoba.com")
    print(f"Password: admin123")
    print(f"Role: Super Admin")
    print(f"\nYou can now log in to the admin dashboard.")
