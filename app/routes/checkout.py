import uuid
from datetime import datetime, timedelta
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import User, Order, PaymentTransaction
from ..utils.helpers import (
    build_validated_delivery_payload,
    resolve_order_items_for_checkout,
    resolve_promotion_for_checkout,
    set_order_payment_state,
    append_order_event,
    build_order_summary_payload
)
from ..utils.mpesa import (
    start_mpesa_stk_push,
    MpesaApiError,
    MpesaValidationError,
)

checkout_bp = Blueprint('checkout', __name__)

@checkout_bp.route('', methods=['POST'])
@jwt_required(optional=True)
def checkout():
    user_id_from_jwt = get_jwt_identity()
    data = request.get_json() or {}
    
    if user_id_from_jwt:
        user_id = int(user_id_from_jwt)
        user = User.query.get(user_id)
    else:
        email = data.get('shipping_address', {}).get('email') or data.get('email')
        phone = data.get('shipping_address', {}).get('phone') or data.get('phone')
        name = data.get('shipping_address', {}).get('name') or data.get('name') or 'Guest'
        
        if not email:
            return jsonify({'message': 'Email address is required for checkout'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                is_guest=True,
                email=email,
                phone=phone,
                name=name,
                username=f"guest_{int(datetime.utcnow().timestamp())}"
            )
            db.session.add(user)
            db.session.commit()
        user_id = user.id

    try:
        shipping_address, delivery_payload, shipping_kes = build_validated_delivery_payload(data)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    checkout_data = dict(data)
    checkout_data['shipping_address'] = shipping_address
    checkout_data['delivery'] = delivery_payload
    
    try:
        order_items = resolve_order_items_for_checkout(user_id, checkout_data)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    try:
        promo_summary = resolve_promotion_for_checkout(user, checkout_data, order_items, shipping_kes)
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    # Pricing constants
    USD_RATE = 128.5
    total_usd = round(float(promo_summary.get('final_total_kes', 0) or 0) / USD_RATE, 2)

    payment_method = checkout_data.get('payment_method', 'card')
    order = Order(
        order_id=str(uuid.uuid4())[:8].upper(),
        user_id=user_id,
        items=order_items,
        total_usd=total_usd,
        shipping_address=shipping_address,
        payment_method=payment_method,
        payment_status='pending',
        order_status='processing',
        promo_code_id=promo_summary.get('promo_code_id'),
        promo_code=promo_summary.get('promo_code'),
        discount_type=promo_summary.get('discount_type'),
        discount_amount=float(promo_summary.get('discount_amount', 0) or 0),
        shipping_discount=float(promo_summary.get('shipping_discount', 0) or 0),
        final_total_after_discount=float(promo_summary.get('final_total_kes', 0) or 0),
    )

    db.session.add(order)
    db.session.flush()
    
    set_order_payment_state(
        order,
        **build_order_summary_payload(checkout_data, user, order_items, total_usd, promo_summary),
    )
    
    append_order_event(
        order,
        event_type='order_created',
        message=f"Order created with {len(order_items)} item(s) totaling KSh {float(promo_summary.get('final_total_kes', 0) or 0):,.0f}.",
        metadata={
            'payment_method': payment_method,
            'item_count': len(order_items),
        },
    )

    if payment_method == 'mpesa':
        grand_total_kes = float(promo_summary.get('final_total_kes', 0) or 0)
        payment_details = data.get('payment_details') or {}
        phone_number = payment_details.get('phone_number') or shipping_address.get('phone') or data.get('phone')

        if grand_total_kes <= 0:
            db.session.rollback()
            return jsonify({'message': 'A valid KES total is required for M-Pesa checkout.'}), 400

        if not phone_number:
            db.session.rollback()
            return jsonify({'message': 'An M-Pesa phone number is required.'}), 400

        pending_transaction = PaymentTransaction.query.filter_by(
            order_id=order.id,
            provider='mpesa',
        ).filter(PaymentTransaction.status.in_(['initiated', 'pending'])).order_by(PaymentTransaction.created_at.desc()).first()

        if pending_transaction:
            # Prevent duplicate STK pushes for the same unpaid order.
            return jsonify({
                'status': 'pending',
                'order_id': order.order_id,
                'checkout_request_id': pending_transaction.provider_reference,
                'merchant_request_id': pending_transaction.merchant_request_id,
                'customer_message': 'A payment request is already pending for this order. Please confirm on your M-Pesa-enabled phone.',
            }), 200

        try:
            stk_response, normalized_phone = start_mpesa_stk_push(
                phone_number=phone_number,
                amount_kes=grand_total_kes,
                order_id=order.order_id,
                description=f"Queen Koba order {order.order_id}",
            )

            payment_tx = PaymentTransaction(
                order_id=order.id,
                provider='mpesa',
                provider_reference=stk_response.get('CheckoutRequestID'),
                merchant_request_id=stk_response.get('MerchantRequestID'),
                account_reference=order.order_id,
                phone_number=normalized_phone,
                amount=float(grand_total_kes),
                status='pending',
                raw_response=stk_response,
            )
            db.session.add(payment_tx)

            set_order_payment_state(
                order,
                checkout_request_id=stk_response.get('CheckoutRequestID'),
                merchant_request_id=stk_response.get('MerchantRequestID'),
                customer_message=stk_response.get('CustomerMessage'),
                phone_number=normalized_phone,
                amount_kes=float(grand_total_kes),
                payment_provider='mpesa',
                payment_status='pending',
            )

            order.payment_status = 'pending'
            order.order_status = 'payment_pending'

            append_order_event(
                order,
                event_type='mpesa_stk_initiated',
                category='payment',
                message=f"M-Pesa STK push initiated to {normalized_phone}.",
                metadata={
                    'phone_number': normalized_phone,
                    'amount_kes': float(grand_total_kes),
                    'checkout_request_id': stk_response.get('CheckoutRequestID'),
                },
            )

            db.session.commit()
            return jsonify({
                'status': 'pending',
                'order_id': order.order_id,
                'checkout_request_id': stk_response.get('CheckoutRequestID'),
                'customer_message': stk_response.get('CustomerMessage'),
                'merchant_request_id': stk_response.get('MerchantRequestID'),
            }), 200

        except MpesaValidationError as error:
            db.session.rollback()
            return jsonify({'message': str(error)}), 400
        except MpesaApiError as error:
            db.session.rollback()
            return jsonify({'message': str(error)}), 502
        except requests.RequestException as error:
            db.session.rollback()
            return jsonify({'message': 'Payment provider unreachable. Try again.'}), 503

    db.session.commit()
    return jsonify({
        'status': 'success',
        'order_id': order.order_id,
        'message': 'Order placed successfully'
    })
