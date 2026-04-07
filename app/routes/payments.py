import structlog
from datetime import datetime
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Order, PaymentTransaction
from ..utils.helpers import (
    get_order_payment_state,
    set_order_payment_state,
    append_order_event,
    record_promotion_usage_for_order,
    now_utc,
    clear_user_cart_items,
)
from ..utils.mpesa import extract_mpesa_callback_metadata

payments_bp = Blueprint('payments', __name__)
log = structlog.get_logger()

def parse_payment_datetime_value(value):
    if value in (None, '', False):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.isdigit() and len(text) == 14:
        try:
            return datetime.strptime(text, '%Y%m%d%H%M%S')
        except ValueError:
            return None
    return None

def find_payment_transaction(checkout_request_id):
    if not checkout_request_id:
        return None
    return PaymentTransaction.query.filter_by(provider='mpesa', provider_reference=checkout_request_id).first()

@payments_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json(silent=True) or {}
    callback = data.get('Body', {}).get('stkCallback', {})
    checkout_request_id = callback.get('CheckoutRequestID')

    log.info('mpesa_callback_received', checkout_request_id=checkout_request_id)

    if not checkout_request_id:
        log.warning('mpesa_callback_missing_checkout_id', payload=data)
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Missing CheckoutRequestID'}), 400

    tx = find_payment_transaction(checkout_request_id)
    if not tx:
        log.warning('mpesa_callback_unknown_transaction', checkout_request_id=checkout_request_id)
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    if tx.status in {'success', 'failed', 'cancelled', 'timeout'} and tx.callback_payload == data:
        log.info('mpesa_callback_idempotent', checkout_request_id=checkout_request_id, status=tx.status)
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    order = Order.query.get(tx.order_id)
    if not order:
        log.error('mpesa_callback_orphan_transaction', checkout_request_id=checkout_request_id)
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

    result_code = callback.get('ResultCode')
    result_desc = callback.get('ResultDesc')
    metadata = extract_mpesa_callback_metadata(callback.get('CallbackMetadata', {}))
    transaction_datetime = parse_payment_datetime_value(metadata.get('TransactionDate'))
    confirmed_at = now_utc().isoformat()

    tx.merchant_request_id = tx.merchant_request_id or metadata.get('MerchantRequestID')
    tx.receipt_number = metadata.get('MpesaReceiptNumber') or tx.receipt_number
    tx.transaction_date = transaction_datetime or tx.transaction_date
    tx.amount = float(metadata.get('Amount') or tx.amount or 0)
    tx.phone_number = str(metadata.get('PhoneNumber') or tx.phone_number)
    tx.result_code = str(result_code)
    tx.result_desc = result_desc
    tx.callback_payload = data

    payment_succeeded = str(result_code) == '0'
    if payment_succeeded:
        tx.status = 'success'
        order.payment_status = 'success'
        order.order_status = 'confirmed'
        set_order_payment_state(
            order,
            result_code=0,
            result_desc=result_desc,
            receipt_number=tx.receipt_number,
            payment_reference=tx.receipt_number,
            transaction_date=metadata.get('TransactionDate'),
            payment_provider='mpesa',
            payment_confirmed_at=confirmed_at,
            paid_at=(transaction_datetime.isoformat() if transaction_datetime else confirmed_at),
            amount_kes=tx.amount,
            callback_payload=data,
        )
        record_promotion_usage_for_order(order)
        clear_user_cart_items(order.user_id)
        log.info('mpesa_payment_confirmed', order_id=order.order_id, receipt=tx.receipt_number)
    else:
        failure_status = 'failed'
        result_desc_text = str(result_desc or '').lower()
        if 'cancelled' in result_desc_text or 'cancel' in result_desc_text:
            failure_status = 'cancelled'
        elif 'timeout' in result_desc_text or 'timed out' in result_desc_text:
            failure_status = 'timeout'

        tx.status = failure_status
        order.payment_status = failure_status
        order.order_status = 'payment_failed'
        set_order_payment_state(
            order,
            result_code=result_code,
            result_desc=result_desc,
            payment_provider='mpesa',
            payment_confirmed_at=get_order_payment_state(order).get('payment_confirmed_at'),
            paid_at=get_order_payment_state(order).get('paid_at'),
            amount_kes=tx.amount,
            callback_payload=data,
        )
        log.warning('mpesa_payment_failed', order_id=order.order_id, result_code=result_code, result_desc=result_desc, status=failure_status)

    append_order_event(
        order,
        event_type='mpesa_callback_received',
        category='payment',
        message=f"M-Pesa callback {'confirmed' if payment_succeeded else 'reported failure'}: {result_desc}",
        metadata={
            'result_code': result_code,
            'result_desc': result_desc,
            'receipt_number': tx.receipt_number,
            'status': tx.status,
        },
    )
    tx.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

@payments_bp.route('/status', methods=['GET'])
@payments_bp.route('/status/<string:order_id>', methods=['GET'])
def get_payment_status(order_id=None):
    query_order_id = order_id or request.args.get('order_id')
    checkout_request_id = request.args.get('checkout_request_id')

    if not query_order_id and not checkout_request_id:
        return jsonify({'error': 'order_id or checkout_request_id is required'}), 400

    order = None
    transaction = None
    if query_order_id:
        order = Order.query.filter_by(order_id=query_order_id).first()
        if order and order.payment_method == 'mpesa':
            transaction = PaymentTransaction.query.filter_by(order_id=order.id, provider='mpesa').order_by(PaymentTransaction.created_at.desc()).first()
    elif checkout_request_id:
        transaction = PaymentTransaction.query.filter_by(provider='mpesa', provider_reference=checkout_request_id).first()
        if transaction:
            order = Order.query.get(transaction.order_id)

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    state = get_order_payment_state(order)
    return jsonify({
        'order_id': order.order_id,
        'payment_status': order.payment_status,
        'order_status': order.order_status,
        'checkout_request_id': state.get('checkout_request_id') or (transaction.provider_reference if transaction else None),
        'merchant_request_id': state.get('merchant_request_id') or (transaction.merchant_request_id if transaction else None),
        'receipt_number': state.get('receipt_number') or (transaction.receipt_number if transaction else None),
        'amount_kes': state.get('amount_kes') or (transaction.amount if transaction else None),
        'payment_provider': state.get('payment_provider') or 'mpesa',
    })
