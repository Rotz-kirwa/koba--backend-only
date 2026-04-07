"""
payment_sync.py
---------------
Fallback background job that queries Safaricom for stuck M-Pesa transactions.
Refactored for modular app architecture.

Usage
-----
  Run standalone:
      python payment_sync.py
"""

import os
import sys
import requests
import structlog
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path to ensure 'app' is importable
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models import PaymentTransaction, Order
from app.utils.helpers import (
    set_order_payment_state,
    append_order_event,
    clear_user_cart_items,
    record_promotion_usage_for_order,
    now_utc
)
from app.utils.mpesa import query_mpesa_stk_status

# Initialize App for context
app = create_app()

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

log = structlog.get_logger()

MIN_AGE_MINUTES = 2    # Only sync transactions older than this
MAX_AGE_MINUTES = 60   # Stop trying after this long
BATCH_LIMIT     = 50   # Max transactions to process per run

def sync_stuck_transactions():
    """Query Safaricom status for all pending M-Pesa transactions."""
    with app.app_context():
        cutoff_old = datetime.now(timezone.utc) - timedelta(minutes=MIN_AGE_MINUTES)
        cutoff_new = datetime.now(timezone.utc) - timedelta(minutes=MAX_AGE_MINUTES)

        stuck = (
            PaymentTransaction.query
            .filter(
                PaymentTransaction.provider == "mpesa",
                PaymentTransaction.status == "pending",
                PaymentTransaction.created_at <= cutoff_old,
                PaymentTransaction.created_at >= cutoff_new,
            )
            .limit(BATCH_LIMIT)
            .all()
        )

        log.info("payment_sync_started", stuck_count=len(stuck))

        for tx in stuck:
            order = Order.query.get(tx.order_id)
            if not order:
                log.warning("payment_sync_order_missing", tx_id=tx.id)
                continue

            if order.payment_status in ("paid", "failed"):
                tx.status = 'completed' if order.payment_status == 'paid' else 'failed'
                tx.updated_at = datetime.utcnow()
                db.session.add(tx)
                continue

            checkout_request_id = tx.provider_reference
            if not checkout_request_id:
                continue

            try:
                query_response = query_mpesa_stk_status(checkout_request_id)
            except (ValueError, requests.RequestException) as err:
                log.warning("payment_sync_query_error", tx_id=tx.id, error=str(err))
                continue

            result_code_raw = query_response.get("ResultCode")
            try:
                result_code = int(result_code_raw)
            except (TypeError, ValueError):
                result_code = result_code_raw
            result_desc = query_response.get("ResultDesc", "")

            if result_code == 0:
                tx.status = "completed"
                tx.raw_response = query_response
                tx.updated_at = datetime.utcnow()

                order.payment_status = "paid"
                order.order_status = "processing"

                set_order_payment_state(
                    order,
                    result_code=result_code,
                    result_desc=result_desc,
                    payment_confirmed_at=now_utc().isoformat(),
                    paid_at=now_utc().isoformat(),
                    query_payload=query_response,
                )
                append_order_event(
                    order,
                    event_type="mpesa_synced_confirmed",
                    category="payment",
                    message="M-Pesa payment confirmed by fallback sync job.",
                )
                clear_user_cart_items(order.user_id)
                record_promotion_usage_for_order(order)
                log.info("payment_sync_confirmed", order_id=order.order_id)

            elif result_code in (1032, 1037, 2001, 1):
                tx.status = "failed"
                tx.raw_response = query_response
                tx.updated_at = datetime.utcnow()

                order.payment_status = "failed"
                order.order_status = "payment_failed"

                set_order_payment_state(
                    order,
                    result_code=result_code,
                    result_desc=result_desc,
                    query_payload=query_response,
                )
                log.warning("payment_sync_failed", order_id=order.order_id, reason=result_desc)
            
            db.session.add(tx)

        db.session.commit()
        log.info("payment_sync_complete")

if __name__ == "__main__":
    sync_stuck_transactions()
