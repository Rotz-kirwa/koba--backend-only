from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PRODUCTS = [
    {
        "id": 1,
        "name": "Complex Clarifier Cream",
        "description": "Luxurious clarifying cream",
        "prices": {
            "KES": 3850,
            "UGX": 107400,
            "BIF": 85400,
            "CDF": 80970
        }
    },
    {
        "id": 2,
        "name": "Complexion Clarifier Serum", 
        "description": "Vitamin C serum",
        "prices": {
            "KES": 4430,
            "UGX": 123500,
            "BIF": 98300,
            "CDF": 93150
        }
    }
]

@app.route('/')
def home():
    return jsonify({"message": "Queen Koba API", "status": "success"})

@app.route('/products')
def products():
    return jsonify({
        "status": "success", 
        "count": len(PRODUCTS),
        "products": PRODUCTS
    })

if __name__ == '__main__':
    print("🚀 Starting Queen Koba API on http://localhost:5000")
    print("📦 Products loaded:", len(PRODUCTS))
    print("💳 Multi-currency prices: KES, UGX, BIF, CDF")
    print("\nPress Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5000, debug=True)
