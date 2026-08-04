# app/utils/currency_utils.py
import requests
from flask import current_app
from datetime import datetime, timedelta

class CurrencyManager:
    """Manage currency conversions and exchange rates"""
    
    # Static exchange rates (update these regularly via API)
    # Based on Trading Economics data for UGX[citation:9]
    DEFAULT_EXCHANGE_RATES = {
        'USD': 1.0,
        'KES': 128.5,      # Kenyan Shilling (approx)
        'UGX': 3582.34,    # Ugandan Shilling[citation:9]
        'BIF': 2850.0,     # Burundi Franc (approx)
        'CDF': 2700.0      # Congolese Franc (approx)
    }
    
    @classmethod
    def convert_price(cls, amount_usd, target_currency):
        """Convert USD amount to target currency"""
        if target_currency.upper() not in cls.DEFAULT_EXCHANGE_RATES:
            raise ValueError(f"Unsupported currency: {target_currency}")
        
        rate = cls.DEFAULT_EXCHANGE_RATES[target_currency.upper()]
        return round(amount_usd * rate, 2)
    
    @classmethod
    def get_all_prices(cls, amount_usd):
        """Get prices in all supported currencies"""
        prices = {}
        for currency, rate in cls.DEFAULT_EXCHANGE_RATES.items():
            if currency != 'USD':
                prices[currency] = {
                    'amount': round(amount_usd * rate, 2),
                    'rate': rate,
                    'symbol': cls.get_currency_symbol(currency)
                }
        return prices
    
    @classmethod
    def get_currency_symbol(cls, currency_code):
        """Get currency symbol"""
        symbols = {
            'KES': 'KSh',
            'UGX': 'USh',
            'BIF': 'FBu',
            'CDF': 'FC',
            'USD': '$'
        }
        return symbols.get(currency_code, currency_code)
    
    @classmethod
    def update_exchange_rates(cls):
        """Update exchange rates from API"""
        try:
            # This would call a real API - using static data for now
            # response = requests.get(current_app.config['CURRENCY_API_URL'])
            # data = response.json()
            # Update DEFAULT_EXCHANGE_RATES with real data
            pass
        except Exception as e:
            current_app.logger.error(f"Failed to update exchange rates: {e}")