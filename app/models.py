# app/models.py - MongoDB schemas (but MongoDB is schemaless)
from datetime import datetime
import uuid
from bson import ObjectId

class ProductSchema:
    """Product schema definition for MongoDB"""
    
    @staticmethod
    def create_product(data):
        """Create a product document"""
        product_id = str(ObjectId())
        
        return {
            '_id': product_id,
            'name': data.get('name'),
            'description': data.get('description'),
            'base_price_usd': float(data.get('base_price_usd', 0)),
            'image_url': data.get('image_url', ''),
            'category': data.get('category', ''),
            'in_stock': data.get('in_stock', True),
            'created_at': datetime.utcnow(),
            'prices': [],  # Will store multi-currency prices
            'metadata': {
                'created_by': data.get('created_by', 'system'),
                'last_updated': datetime.utcnow()
            }
        }
    
    @staticmethod
    def add_price_to_product(product, currency_data):
        """Add price in specific currency to product"""
        if 'prices' not in product:
            product['prices'] = []
        
        price_entry = {
            'currency_code': currency_data['currency_code'],
            'price': float(currency_data['price']),
            'country': currency_data.get('country', ''),
            'symbol': currency_data.get('symbol', ''),
            'updated_at': datetime.utcnow()
        }
        
        # Update if currency already exists, else append
        updated = False
        for i, price in enumerate(product.get('prices', [])):
            if price['currency_code'] == currency_data['currency_code']:
                product['prices'][i] = price_entry
                updated = True
                break
        
        if not updated:
            product['prices'].append(price_entry)
        
        return product

class UserSchema:
    """User schema definition for MongoDB"""
    
    @staticmethod
    def create_user(data):
        """Create a user document"""
        import bcrypt
        
        user_id = str(ObjectId())
        password = data.get('password', '').encode('utf-8')
        
        return {
            '_id': user_id,
            'username': data.get('username'),
            'email': data.get('email'),
            'password_hash': bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8'),
            'country': data.get('country', 'Kenya'),
            'preferred_currency': data.get('preferred_currency', 'KES'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'role': data.get('role', 'customer')
        }
    
    @staticmethod
    def check_password(stored_hash, password):
        """Check if password matches hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

class CurrencyManager:
    """Manage currency conversions (same as before but adapted for MongoDB)"""
    
    # Exchange rates (approximate)
    EXCHANGE_RATES = {
        'USD': 1.0,
        'KES': 128.5,      # Kenyan Shilling
        'UGX': 3582.34,    # Ugandan Shilling
        'BIF': 2850.0,     # Burundi Franc
        'CDF': 2700.0      # Congolese Franc
    }
    
    CURRENCY_SYMBOLS = {
        'KES': 'KSh',
        'UGX': 'USh',
        'BIF': 'FBu',
        'CDF': 'FC',
        'USD': '$'
    }
    
    @classmethod
    def convert_price(cls, amount_usd, target_currency):
        """Convert USD amount to target currency"""
        currency = target_currency.upper()
        if currency not in cls.EXCHANGE_RATES:
            raise ValueError(f"Unsupported currency: {currency}")
        
        rate = cls.EXCHANGE_RATES[currency]
        return round(amount_usd * rate, 2)
    
    @classmethod
    def get_all_prices(cls, amount_usd):
        """Get prices in all supported currencies"""
        prices = {}
        for currency, rate in cls.EXCHANGE_RATES.items():
            if currency != 'USD':
                prices[currency] = {
                    'amount': round(amount_usd * rate, 2),
                    'rate': rate,
                    'symbol': cls.CURRENCY_SYMBOLS.get(currency, currency)
                }
        return prices
    
    @classmethod
    def get_country_currency(cls, country):
        """Get currency for a specific country"""
        country_currency_map = {
            'Kenya': 'KES',
            'Uganda': 'UGX',
            'Burundi': 'BIF',
            'DRC Congo': 'CDF',
            'Tanzania': 'TZS',
            'Rwanda': 'RWF'
        }
        return country_currency_map.get(country, 'USD')