from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Queen Koba products with multi-currency prices
PRODUCTS = [
    {
        "id": 1,
        "name": "Complexion Clarifier Cream",
        "description": "A luxurious cream that gently clarifies and purifies complexion",
        "category": "Cream",
        "in_stock": True,
        "prices": {
            "KES": {"amount": 3850, "symbol": "KSh", "country": "Kenya"},
            "UGX": {"amount": 107400, "symbol": "USh", "country": "Uganda"},
            "BIF": {"amount": 85400, "symbol": "FBu", "country": "Burundi"},
            "CDF": {"amount": 80970, "symbol": "FC", "country": "DRC Congo"}
        }
    },
    {
        "id": 2,
        "name": "Complexion Clarifier Serum",
        "description": "Powerful serum with Vitamin C and Niacinamide",
        "category": "Serum",
        "in_stock": True,
        "prices": {
            "KES": {"amount": 4430, "symbol": "KSh", "country": "Kenya"},
            "UGX": {"amount": 123500, "symbol": "USh", "country": "Uganda"},
            "BIF": {"amount": 98300, "symbol": "FBu", "country": "Burundi"},
            "CDF": {"amount": 93150, "symbol": "FC", "country": "DRC Congo"}
        }
    },
    {
        "id": 3,
        "name": "Complexion Clarifying Mask",
        "description": "Detoxifying clay mask with Charcoal and Tea Tree Oil",
        "category": "Mask",
        "in_stock": True,
        "prices": {
            "KES": {"amount": 3308, "symbol": "KSh", "country": "Kenya"},
            "UGX": {"amount": 92200, "symbol": "USh", "country": "Uganda"},
            "BIF": {"amount": 73400, "symbol": "FBu", "country": "Burundi"},
            "CDF": {"amount": 69525, "symbol": "FC", "country": "DRC Congo"}
        }
    }
]

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to Queen Koba Skincare API",
        "status": "success",
        "version": "1.0",
        "endpoints": {
            "GET /": "API information",
            "GET /products": "All products with multi-currency prices",
            "GET /products/<id>": "Single product details",
            "GET /currencies": "Available currencies"
        }
    })

@app.route('/products')
def get_products():
    return jsonify({
        "status": "success",
        "count": len(PRODUCTS),
        "products": PRODUCTS
    })

@app.route('/products/<int:product_id>')
def get_product(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        return jsonify({
            "status": "success",
            "product": product
        })
    return jsonify({"error": "Product not found"}), 404

@app.route('/currencies')
def get_currencies():
    currencies = [
        {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh", "country": "Kenya"},
        {"code": "UGX", "name": "Ugandan Shilling", "symbol": "USh", "country": "Uganda"},
        {"code": "BIF", "name": "Burundi Franc", "symbol": "FBu", "country": "Burundi"},
        {"code": "CDF", "name": "Congolese Franc", "symbol": "FC", "country": "DRC Congo"}
    ]
    return jsonify({
        "status": "success",
        "currencies": currencies
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Queen Koba API",
        "timestamp": "running"
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("   QUEEN KOBA SKINCARE API")
    print("="*50)
    print("\n📦 Products Available:")
    for product in PRODUCTS:
        print(f"   • {product['name']}")
    
    print("\n💱 Multi-Currency Pricing:")
    print("   KES (Kenyan Shilling) - Kenya")
    print("   UGX (Ugandan Shilling) - Uganda")
    print("   BIF (Burundi Franc) - Burundi")
    print("   CDF (Congolese Franc) - DRC Congo")
    
    print("\n🌐 Server URLs:")
    print("   Local:    https://localhost:5000")
    print("   Network:  https://0.0.0.0:5000")
    
    print("\n📚 API Endpoints:")
    print("   GET /              - API information")
    print("   GET /products      - All products")
    print("   GET /currencies    - Available currencies")
    print("   GET /health        - Health check")
    
    print("\n" + "="*50)
    print("🚀 Starting server... (Press Ctrl+C to stop)")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
