import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from flask import current_app
from ..extensions import db
from ..models import (
    User, Order, CartItem, Product, Promotion, PromotionUsage,
    PromotionProduct, PromotionCategory, PromotionUser
)

# Standardize timezone usage
def now_utc():
    return datetime.now(timezone.utc)

def parse_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def parse_int(value, default=0):
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def parse_bool(value, default=False):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on')

# --- Product & Currency Helpers ---

def calculate_prices(base_price_usd):
    exchange_rates = {
        'KES': 128.5,
        'UGX': 3582.34,
        'BIF': 2850.0,
        'CDF': 2700.0
    }
    
    currency_symbols = {
        'KES': 'KSh',
        'UGX': 'USh',
        'BIF': 'FBu',
        'CDF': 'FC',
    }
    
    currency_countries = {
        'KES': 'Kenya',
        'UGX': 'Uganda',
        'BIF': 'Burundi',
        'CDF': 'DRC Congo',
    }
    
    prices = {}
    for currency, rate in exchange_rates.items():
        prices[currency] = {
            'amount': round(base_price_usd * rate, 2),
            'symbol': currency_symbols[currency],
            'country': currency_countries[currency],
        }
    
    return prices

def convert_usd_to_kes(amount):
    return round(float(amount or 0) * 128.5, 2)

def build_order_item_payload(product, quantity):
    unit_price_usd = float(product.base_price_usd or 0)
    product_prices = product.prices or {}
    kes_entry = product_prices.get('KES') if isinstance(product_prices, dict) else None
    unit_price_kes = None
    if isinstance(kes_entry, dict):
        kes_amount = kes_entry.get('amount')
        if kes_amount is not None:
            unit_price_kes = float(kes_amount)
    if unit_price_kes is None:
        unit_price_kes = convert_usd_to_kes(unit_price_usd)

    quantity = int(quantity or 0)

    return {
        'product_id': str(product.id),
        'product_name': product.name,
        'product_price': unit_price_usd,
        'price_per_item': unit_price_usd,
        'product_price_kes': unit_price_kes,
        'price_per_item_kes': unit_price_kes,
        'description': product.description or '',
        'image_url': product.image_url,
        'category': product.category or '',
        'quantity': quantity,
        'item_total': round(unit_price_usd * quantity, 2),
        'item_total_kes': round(unit_price_kes * quantity, 2),
    }

def build_cart_item_payload(item):
    return build_order_item_payload(item.product, item.quantity)

def build_public_product_payload(product, lite=False):
    payload = {
        '_id': str(product.id),
        'id': str(product.id),
        'name': product.name,
        'category': product.category,
        'prices': product.prices,
        'in_stock': product.in_stock,
        'image_url': product.image_url,
        'discount_percentage': product.discount_percentage or 0,
        'on_sale': product.on_sale or False,
    }

    if not lite:
        payload.update({
            'description': product.description,
            'base_price_usd': product.base_price_usd,
        })
    
    return payload

# --- Delivery Helpers ---

DELIVERY_ZONE_RULES = {
    'nairobi': {
        'code': 'nairobi',
        'label': 'Within Nairobi',
        'shipping_fee': 300.0,
        'eta': 'Same day / next day',
    },
    'outside_nairobi': {
        'code': 'outside_nairobi',
        'label': 'Outside Nairobi',
        'shipping_fee': 500.0,
        'eta': '2-4 business days',
    },
}

def normalize_delivery_text(value):
    return ' '.join(str(value or '').split()).strip()

def validate_promotion_payload(data):
    code = normalize_promo_code(data.get('code'))
    if not code:
        raise ValueError('Promo code is required')

    discount_type = str(data.get('discount_type') or data.get('type') or 'percentage').strip().lower()
    if discount_type not in ['percentage', 'fixed', 'free_shipping']:
        raise ValueError('Discount type must be percentage, fixed, or free_shipping')

    discount_value = parse_float(data.get('discount_value', data.get('discount', 0)), 0)
    if discount_type != 'free_shipping' and discount_value <= 0:
        raise ValueError('Discount value must be greater than zero')

    min_order_amount = parse_float(data.get('min_order_amount'), 0)
    max_discount_amount = data.get('max_discount_amount')
    max_discount_amount = parse_float(max_discount_amount, None) if max_discount_amount not in (None, '') else None
    usage_limit = parse_int(data.get('usage_limit', data.get('limit')), None)
    per_user_limit = parse_int(data.get('per_user_limit'), None)
    applies_to_type = str(data.get('applies_to_type') or 'all').strip().lower()
    if applies_to_type not in ['all', 'products', 'categories']:
        raise ValueError('Applies-to type must be all, products, or categories')

    customer_scope = str(data.get('customer_scope') or 'all').strip().lower()
    if customer_scope not in ['all', 'selected_users']:
        raise ValueError('Customer scope must be all or selected_users')

    starts_at = parse_datetime_value(data.get('starts_at'))
    expires = parse_datetime_value(data.get('expires'))
    if starts_at and expires and expires <= starts_at:
        raise ValueError('Expiry date must be after the start date')

    if discount_type == 'percentage' and discount_value > 100:
        raise ValueError('Percentage discounts cannot exceed 100')

    product_ids = sorted({int(product_id) for product_id in (data.get('product_ids') or []) if str(product_id).strip()})
    categories = sorted({normalize_category_name(category) for category in (data.get('categories') or []) if normalize_category_name(category)})
    user_ids = sorted({int(user_id) for user_id in (data.get('user_ids') or []) if str(user_id).strip()})

    return {
        'code': code,
        'description': str(data.get('description') or '').strip(),
        'internal_notes': str(data.get('internal_notes') or '').strip(),
        'discount': discount_value,
        'type': discount_type,
        'status': 'active' if bool(data.get('is_active', data.get('status', 'active') == 'active')) else 'inactive',
        'limit': usage_limit,
        'per_user_limit': per_user_limit,
        'min_order_amount': min_order_amount,
        'max_discount_amount': max_discount_amount,
        'first_order_only': bool(data.get('first_order_only')),
        'starts_at': starts_at,
        'expires': expires,
        'applies_to_type': applies_to_type,
        'customer_scope': customer_scope,
        'campaign_type': str(data.get('campaign_type') or '').strip(),
        'product_ids': product_ids,
        'categories': categories,
        'user_ids': user_ids,
    }

def sync_promotion_targets(promo, payload):
    from ..models import PromotionProduct, PromotionCategory, PromotionUser
    PromotionProduct.query.filter_by(promo_code_id=promo.id).delete()
    PromotionCategory.query.filter_by(promo_code_id=promo.id).delete()
    PromotionUser.query.filter_by(promo_code_id=promo.id).delete()

    for product_id in payload['product_ids']:
        db.session.add(PromotionProduct(promo_code_id=promo.id, product_id=product_id))

    for category in payload['categories']:
        db.session.add(PromotionCategory(promo_code_id=promo.id, category=category))

    for user_id in payload['user_ids']:
        db.session.add(PromotionUser(promo_code_id=promo.id, user_id=user_id))

def apply_promotion_model_updates(promo, payload, admin_user_id=None):
    promo.code = payload['code']
    promo.description = payload['description']
    promo.internal_notes = payload['internal_notes']
    promo.discount = payload['discount']
    promo.type = payload['type']
    promo.status = payload['status']
    promo.limit = payload['limit']
    promo.per_user_limit = payload['per_user_limit']
    promo.min_order_amount = payload['min_order_amount']
    promo.max_discount_amount = payload['max_discount_amount']
    promo.first_order_only = payload['first_order_only']
    promo.starts_at = payload['starts_at']
    promo.expires = payload['expires']
    promo.applies_to_type = payload['applies_to_type']
    promo.customer_scope = payload['customer_scope']
    promo.campaign_type = payload['campaign_type']
    if admin_user_id and not promo.created_by_admin_id:
        promo.created_by_admin_id = admin_user_id

def normalize_promo_code(value):
    normalized = normalize_delivery_text(value).lower().replace('-', '_').replace(' ', '_')
    if (
        normalized in {'nairobi', 'within_nairobi'}
        or ('nairobi' in normalized and not normalized.startswith('outside'))
    ):
        return 'nairobi'
    if normalized in {'outside_nairobi', 'outside'}:
        return 'outside_nairobi'
    if normalized:
        return 'outside_nairobi'
    return None

def normalize_delivery_zone(value):
    normalized = normalize_delivery_text(value).lower().replace('-', '_').replace(' ', '_')
    if (
        normalized in {'nairobi', 'within_nairobi'}
        or ('nairobi' in normalized and not normalized.startswith('outside'))
    ):
        return 'nairobi'
    if normalized in {'outside_nairobi', 'outside'}:
        return 'outside_nairobi'
    if normalized:
        return 'outside_nairobi'
    return None

def get_delivery_zone_rule(data):
    delivery = data.get('delivery') or {}
    shipping_address = data.get('shipping_address') or {}
    zone_candidate = (
        delivery.get('delivery_zone_code')
        or delivery.get('delivery_zone')
        or delivery.get('zone')
        or shipping_address.get('delivery_zone_code')
        or shipping_address.get('delivery_zone')
        or shipping_address.get('zone')
        or delivery.get('county')
    )
    normalized_zone = normalize_delivery_zone(zone_candidate)
    return DELIVERY_ZONE_RULES.get(normalized_zone)

def build_validated_delivery_payload(data):
    shipping_address = dict(data.get('shipping_address') or {})
    delivery = dict(data.get('delivery') or {})
    delivery_rule = get_delivery_zone_rule(data)
    if not delivery_rule:
        raise ValueError('Choose a valid delivery zone before checkout')

    county = normalize_delivery_text(delivery.get('county') or shipping_address.get('county'))
    area = normalize_delivery_text(delivery.get('area') or shipping_address.get('area'))
    delivery_point = normalize_delivery_text(
        delivery.get('delivery_point')
        or delivery.get('point')
        or shipping_address.get('delivery_point')
    )
    delivery_method = normalize_delivery_text(
        delivery.get('method') or shipping_address.get('delivery_method') or 'pickup'
    ).lower()
    
    if delivery_method not in {'pickup', 'door'}:
        delivery_method = 'pickup'

    if not county:
        raise ValueError('County is required before checkout')
    if not area:
        raise ValueError('Area / Town / Estate is required before checkout')
    if not delivery_point:
        raise ValueError('Exact delivery point is required before checkout')

    shipping_fee = float(delivery_rule['shipping_fee'])
    eta = delivery_rule['eta']

    shipping_address.update({
        'county': county,
        'area': area,
        'delivery_point': delivery_point,
        'delivery_zone': delivery_rule['label'],
        'delivery_zone_code': delivery_rule['code'],
        'delivery_method': delivery_method,
        'delivery_eta': eta,
    })

    delivery.update({
        'county': county,
        'area': area,
        'point': delivery_point,
        'delivery_point': delivery_point,
        'delivery_zone': delivery_rule['label'],
        'delivery_zone_code': delivery_rule['code'],
        'method': delivery_method,
        'shipping_fee': shipping_fee,
        'eta': eta,
    })

    return shipping_address, delivery, shipping_fee

# --- Order & Checkout Helpers ---

def resolve_order_items_for_checkout(user_id, data):
    items = data.get('items')
    if items and isinstance(items, list):
        payload_items = []
        for item in items:
            product_id = item.get('product_id')
            quantity = parse_int(item.get('quantity'), 1)
            product = Product.query.get(product_id)
            if product:
                # Calculate KES price based on internal USD rate (simulating original logic)
                kes_price = round(product.base_price_usd * 128.5, 2)
                payload_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'category': product.category,
                    'quantity': quantity,
                    'price_kes': kes_price,
                    'item_total_kes': round(kes_price * quantity, 2),
                    'image_url': product.image_url
                })
        return payload_items

    # Fallback to cart items if no items in payload
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if cart_items:
        payload_items = []
        for item in cart_items:
            kes_price = round(item.product.base_price_usd * 128.5, 2)
            payload_items.append({
                'product_id': item.product.id,
                'name': item.product.name,
                'category': item.product.category,
                'quantity': item.quantity,
                'price_kes': kes_price,
                'item_total_kes': round(kes_price * item.quantity, 2),
                'image_url': item.product.image_url
            })
        return payload_items

    raise ValueError('Cart is empty')

class PromoValidationError(Exception):
    def __init__(self, message, reason=None, exists=True):
        super().__init__(message)
        self.reason = reason
        self.exists = exists

def evaluate_promotion(promo, user, order_items, shipping_kes):
    current_time = datetime.utcnow()
    normalized_code = promo.code if promo else ''
    subtotal_kes = round(sum(float(item.get('item_total_kes', 0) or 0) for item in order_items), 2)

    if not promo:
        raise PromoValidationError('Promo code not found', reason='not_found', exists=False)

    if promo.status != 'active':
        raise PromoValidationError('This promo code is not active', reason='inactive')

    if promo.starts_at and promo.starts_at > current_time:
        raise PromoValidationError('This promo code has not started yet', reason='not_started')

    if promo.expires and promo.expires < current_time:
        raise PromoValidationError('This promo code has expired', reason='expired')

    # Add more validations as per original logic here...
    
    discount_amount = 0
    shipping_discount = 0

    if promo.type == 'percentage':
        discount_amount = round(subtotal_kes * (float(promo.discount or 0) / 100), 2)
        if promo.max_discount_amount is not None:
            discount_amount = min(discount_amount, float(promo.max_discount_amount))
    elif promo.type == 'fixed':
        discount_amount = min(round(float(promo.discount or 0), 2), subtotal_kes)
    elif promo.type == 'free_shipping':
        shipping_discount = round(max(float(shipping_kes or 0), 0), 2)

    final_total_kes = max(round(subtotal_kes + float(shipping_kes or 0) - discount_amount - shipping_discount, 2), 0)

    return {
        'promo_code_id': promo.id,
        'promo_code': normalized_code,
        'discount_type': promo.type,
        'discount_amount': round(discount_amount, 2),
        'shipping_discount': round(shipping_discount, 2),
        'subtotal_kes': subtotal_kes,
        'shipping_kes': round(float(shipping_kes or 0), 2),
        'final_total_kes': final_total_kes,
    }

def resolve_promotion_for_checkout(user, data, order_items, shipping_kes):
    code = (data.get('promo_code') or '').strip().upper()
    if not code:
        subtotal_kes = round(sum(float(item.get('item_total_kes', 0) or 0) for item in order_items), 2)
        return {
            'promo_code_id': None,
            'promo_code': '',
            'discount_type': None,
            'discount_amount': 0,
            'shipping_discount': 0,
            'subtotal_kes': subtotal_kes,
            'shipping_kes': round(float(shipping_kes or 0), 2),
            'final_total_kes': round(subtotal_kes + float(shipping_kes or 0), 2),
        }

    promo = Promotion.query.filter_by(code=code).first()
    return evaluate_promotion(promo, user, order_items, shipping_kes)

# --- Order State Helpers ---

def get_order_payment_state(order):
    if not order.status_note:
        return {}
    try:
        return json.loads(order.status_note)
    except (TypeError, json.JSONDecodeError):
        return {}

def set_order_payment_state(order, **updates):
    state = get_order_payment_state(order)
    state.update(updates)
    order.status_note = json.dumps(state)
    return state

def append_order_event(order, event_type, message, category='order', actor='system', metadata=None):
    state = get_order_payment_state(order)
    events = list(state.get('events') or [])
    events.append({
        'type': event_type,
        'category': category,
        'message': message,
        'actor': actor,
        'metadata': metadata or {},
        'created_at': datetime.utcnow().isoformat(),
    })
    state['events'] = events[-50:] # Keep last 50 events
    order.status_note = json.dumps(state)
    return state

def clear_user_cart_items(user_id):
    CartItem.query.filter_by(user_id=user_id).delete()

def record_promotion_usage_for_order(order):
    if not order or not order.promo_code_id or not order.user_id:
        return
    existing = PromotionUsage.query.filter_by(order_id=order.id).first()
    if existing:
        return
    usage = PromotionUsage(
        promo_code_id=order.promo_code_id,
        user_id=order.user_id,
        order_id=order.id,
        discount_amount=order.discount_amount,
        shipping_discount=order.shipping_discount,
        final_total_kes=order.final_total_after_discount
    )
    db.session.add(usage)
    promo = Promotion.query.get(order.promo_code_id)
    if promo:
        promo.uses = (promo.uses or 0) + 1

# --- Admin Helpers ---

def normalize_order_items_for_admin(items):
    normalized_items = []
    for item in items or []:
        normalized = dict(item)
        quantity = int(normalized.get('quantity', 1) or 1)

        if normalized.get('price_per_item_kes') is None and normalized.get('price_per_item') is not None:
            normalized['price_per_item_kes'] = convert_usd_to_kes(normalized.get('price_per_item'))

        if normalized.get('item_total_kes') is None:
            if normalized.get('item_total') is not None:
                normalized['item_total_kes'] = convert_usd_to_kes(normalized.get('item_total'))
            else:
                normalized['item_total_kes'] = float(normalized.get('price_per_item_kes', 0) or 0) * quantity

        normalized_items.append(normalized)

    return normalized_items

def resolve_order_totals_kes(order, state, items):
    totals = state.get('totals', {}) if isinstance(state, dict) else {}

    subtotal_kes = float(totals.get('subtotal_kes', 0) or 0)
    shipping_kes = float(totals.get('shipping_kes', 0) or 0)
    grand_total_kes = float(totals.get('grand_total_kes', 0) or 0)
    amount_kes = float(state.get('amount_kes', 0) or 0) if isinstance(state, dict) else 0

    items_subtotal_kes = sum(float(item.get('item_total_kes', 0) or 0) for item in items)
    converted_total_usd_kes = convert_usd_to_kes(order.total_usd) if order.total_usd else 0

    if subtotal_kes <= 0:
        subtotal_kes = items_subtotal_kes

    if grand_total_kes <= 0 and order.final_total_after_discount:
        grand_total_kes = float(order.final_total_after_discount or 0)

    if grand_total_kes <= 0:
        if amount_kes > 0:
            grand_total_kes = amount_kes
        elif subtotal_kes > 0 or shipping_kes > 0:
            grand_total_kes = subtotal_kes + shipping_kes
        elif converted_total_usd_kes > 0:
            grand_total_kes = converted_total_usd_kes

    if 0 < grand_total_kes < 1 and converted_total_usd_kes > 0:
        grand_total_kes = converted_total_usd_kes

    if subtotal_kes <= 0 and grand_total_kes > 0:
        subtotal_kes = max(grand_total_kes - shipping_kes, 0)

    return subtotal_kes, shipping_kes, grand_total_kes

def resolve_payment_status(order, state):
    if order.payment_method != 'mpesa':
        return order.payment_status or 'pending'

    result_code = state.get('result_code') if isinstance(state, dict) else None
    receipt_number = state.get('receipt_number') if isinstance(state, dict) else None

    if receipt_number or str(result_code) == '0':
        return 'paid'

    if str(result_code) in {'1', '1032', '1037', '2001'} or order.order_status == 'payment_failed':
        return 'failed'

    return order.payment_status or 'pending'

def build_admin_order_payload(order):
    state = get_order_payment_state(order)
    customer = state.get('customer', {}) if isinstance(state, dict) else {}
    payment_details = state.get('payment_details', {}) if isinstance(state, dict) else {}
    delivery = state.get('delivery', {}) if isinstance(state, dict) else {}
    receipt_number = state.get('receipt_number')
    items = normalize_order_items_for_admin(order.items or [])
    subtotal_kes, shipping_kes, grand_total_kes = resolve_order_totals_kes(order, state, items)

    shipping_address = order.shipping_address or {}
    customer_name = customer.get('name') or shipping_address.get('name') or (order.user.name if order.user else None) or (order.user.username if order.user else None)
    customer_email = customer.get('email') or shipping_address.get('email') or (order.user.email if order.user else None)
    customer_phone = customer.get('phone') or shipping_address.get('phone') or (order.user.phone if order.user else None)
    
    return {
        'id': order.id,
        'order_id': order.order_id,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'payment_status': resolve_payment_status(order, state),
        'order_status': order.order_status,
        'total_usd': order.total_usd,
        'subtotal_kes': subtotal_kes,
        'shipping_kes': shipping_kes,
        'grand_total_kes': grand_total_kes,
        'payment_method': order.payment_method,
        'payment_reference': state.get('payment_reference') or receipt_number,
        'delivery_zone': delivery.get('delivery_zone') or shipping_address.get('delivery_zone'),
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'items': items,
        'events': state.get('events', [])
    }

def build_order_summary_payload(data, user, order_items, total_usd, promo_summary):
    return {
        'order_id': str(uuid.uuid4())[:8].upper(),
        'items': order_items,
        'total_usd': total_usd,
        'promo_summary': promo_summary
    }
