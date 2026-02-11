#!/usr/bin/env python3
from pymongo import MongoClient
import bcrypt
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['queenkoba']

print("🗑️  Clearing all mock data from Queen Koba database...\n")

# Clear all collections
collections_to_clear = [
    'products',
    'orders',
    'users',
    'promotions',
    'reviews',
    'shipping_zones',
    'site_content',
    'support_tickets'
]

for collection in collections_to_clear:
    count = db[collection].count_documents({})
    if count > 0:
        db[collection].delete_many({})
        print(f"✅ Cleared {count} documents from '{collection}'")
    else:
        print(f"⚪ '{collection}' was already empty")

print("\n" + "="*50)
print("Creating super admin user...")
print("="*50 + "\n")

# Create super admin user
admin = {
    'username': 'Queen Koba Admin',
    'email': 'admin@queenkoba.com',
    'password_hash': bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode(),
    'role': 'super_admin',
    'permissions': ['*'],
    'status': 'active',
    'created_at': datetime.utcnow()
}

db.users.insert_one(admin)

print("✅ Super Admin created successfully!")
print(f"   Email: admin@queenkoba.com")
print(f"   Password: admin123")
print(f"   Role: super_admin")

print("\n" + "="*50)
print("✨ Database cleared! Ready for fresh data.")
print("="*50)
