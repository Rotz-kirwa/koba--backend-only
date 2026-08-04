# app/routes/currency.py
from flask import Blueprint, jsonify, request
from app.models import Currency, Product, ProductPrice, CurrencyManager
from app import db

currency_bp = Blueprint('currency', __name__, url_prefix='/api')

@currency_bp.route('/products/<int:product_id>/prices', methods=['GET'])
def get_product_prices(product_id):
    """Get product prices in all currencies"""
    product = Product.query.get_or_404(product_id)
    
    # Get all prices for this product
    prices = ProductPrice.query.filter_by(product_id=product_id).all()
    
    # If no prices exist, generate them from base USD price
    if not prices:
        prices_data = CurrencyManager.get_all_prices(product.base_price_usd)
        
        # Save to database
        for currency_code, price_info in prices_data.items():
            country_map = {
                'KES': 'Kenya',
                'UGX': 'Uganda',
                'BIF': 'Burundi',
                'CDF': 'DRC Congo'
            }
            
            product_price = ProductPrice(
                product_id=product_id,
                currency_code=currency_code,
                price=price_info['amount'],
                country=country_map.get(currency_code)
            )
            db.session.add(product_price)
        
        db.session.commit()
        prices = ProductPrice.query.filter_by(product_id=product_id).all()
    
    return jsonify({
        'status': 'success',
        'product_id': product_id,
        'product_name': product.name,
        'base_price_usd': product.base_price_usd,
        'prices': [price.to_dict() for price in prices]
    })

@currency_bp.route('/products/<int:product_id>/price/<currency_code>', methods=['GET'])
def get_product_price_currency(product_id, currency_code):
    """Get product price in specific currency"""
    product = Product.query.get_or_404(product_id)
    
    price = ProductPrice.query.filter_by(
        product_id=product_id,
        currency_code=currency_code.upper()
    ).first()
    
    if not price:
        # Calculate price
        converted_price = CurrencyManager.convert_price(
            product.base_price_usd,
            currency_code.upper()
        )
        
        country_map = {
            'KES': 'Kenya',
            'UGX': 'Uganda',
            'BIF': 'Burundi',
            'CDF': 'DRC Congo'
        }
        
        price = ProductPrice(
            product_id=product_id,
            currency_code=currency_code.upper(),
            price=converted_price,
            country=country_map.get(currency_code.upper())
        )
        db.session.add(price)
        db.session.commit()
    
    return jsonify({
        'status': 'success',
        'product': product.name,
        'currency': currency_code.upper(),
        'price': price.price,
        'symbol': CurrencyManager.get_currency_symbol(currency_code.upper()),
        'country': price.country
    })

@currency_bp.route('/convert-price', methods=['GET'])
def convert_price():
    """Convert price between currencies"""
    amount = float(request.args.get('amount', 0))
    from_currency = request.args.get('from', 'USD').upper()
    to_currency = request.args.get('to', 'KES').upper()
    
    # First convert to USD if not already USD
    if from_currency != 'USD':
        # In real implementation, use proper conversion
        # This is simplified
        amount_usd = amount / CurrencyManager.DEFAULT_EXCHANGE_RATES.get(from_currency, 1)
    else:
        amount_usd = amount
    
    # Convert to target currency
    converted = CurrencyManager.convert_price(amount_usd, to_currency)
    
    return jsonify({
        'status': 'success',
        'original': {
            'amount': amount,
            'currency': from_currency,
            'symbol': CurrencyManager.get_currency_symbol(from_currency)
        },
        'converted': {
            'amount': converted,
            'currency': to_currency,
            'symbol': CurrencyManager.get_currency_symbol(to_currency)
        },
        'exchange_rate': CurrencyManager.DEFAULT_EXCHANGE_RATES.get(to_currency, 1)
    })