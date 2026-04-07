import os
import base64
import requests
from datetime import datetime
import structlog

logger = structlog.get_logger()

class MpesaApiError(Exception):
    pass

class MpesaConfigurationError(MpesaApiError):
    pass

class MpesaValidationError(MpesaApiError):
    pass

def get_mpesa_base_url():
    env = os.getenv('M_PESA_ENV', 'production').lower()
    if env == 'sandbox':
        return 'https://sandbox.safaricom.co.ke'
    return 'https://api.safaricom.co.ke'

def get_mpesa_config():
    return {
        'consumer_key': os.getenv('M_PESA_CONSUMER_KEY', '').strip(),
        'consumer_secret': os.getenv('M_PESA_CONSUMER_SECRET', '').strip(),
        'shortcode': os.getenv('M_PESA_SHORTCODE', '').strip(),
        'passkey': os.getenv('M_PESA_PASSKEY', '').strip(),
        'callback_url': os.getenv('M_PESA_CALLBACK_URL', '').strip(),
        'transaction_type': os.getenv('M_PESA_TRANSACTION_TYPE', 'CustomerPayBillOnline').strip(),
        'account_reference': os.getenv('M_PESA_ACCOUNT_REFERENCE', 'QueenKoba').strip(),
        'timeout_seconds': int(os.getenv('M_PESA_TIMEOUT_SECONDS', '30') or 30),
    }

def mpesa_is_configured():
    config = get_mpesa_config()
    required = ['consumer_key', 'consumer_secret', 'shortcode', 'passkey', 'callback_url']
    return all(config.get(key) for key in required)

def get_mpesa_timestamp():
    return datetime.utcnow().strftime('%Y%m%d%H%M%S')

def build_mpesa_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode('utf-8')).decode('utf-8')

def normalize_mpesa_phone(phone_number):
    digits = ''.join(ch for ch in str(phone_number or '') if ch.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        digits = f"254{digits[1:]}"
    elif digits.startswith('7') and len(digits) == 9:
        digits = f"254{digits}"
    elif digits.startswith('1') and len(digits) == 9:
        digits = f"254{digits}"

    if len(digits) != 12 or not digits.startswith('254'):
        raise ValueError('M-Pesa phone number must be in the format 2547XXXXXXXX or 2541XXXXXXXX')

    return digits

def get_mpesa_access_token():
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise MpesaConfigurationError(
            'M-Pesa is not fully configured. Verify consumer key, consumer secret, shortcode, passkey, and callback URL.'
        )

    credentials = f"{config['consumer_key']}:{config['consumer_secret']}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    try:
        response = requests.get(
            f"{get_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials",
            headers={'Authorization': f"Basic {encoded}"},
            timeout=config['timeout_seconds'],
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as exc:
        logger.error('mpesa_token_timeout', error=str(exc))
        raise MpesaApiError('M-Pesa authentication timed out. Please try again later.') from exc
    except requests.RequestException as exc:
        logger.error('mpesa_token_error', status_code=getattr(exc.response, 'status_code', None), error=str(exc))
        raise MpesaApiError('Unable to authenticate with M-Pesa. Please verify credentials and try again.') from exc
    except ValueError as exc:
        logger.error('mpesa_token_parse_error', error=str(exc))
        raise MpesaApiError('Invalid response from M-Pesa authentication service.') from exc

    token = data.get('access_token')
    if not token:
        logger.error('mpesa_token_missing', response_data=data)
        raise MpesaApiError('M-Pesa authentication failed. Missing access token.')
    return token


def start_mpesa_stk_push(phone_number, amount_kes, order_id, description='Queen Koba order payment'):
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise MpesaConfigurationError(
            'M-Pesa is not fully configured. Verify consumer key, consumer secret, shortcode, passkey, and callback URL.'
        )

    if amount_kes is None:
        raise MpesaValidationError('M-Pesa amount is required.')

    try:
        amount = int(round(float(amount_kes)))
    except (ValueError, TypeError) as exc:
        logger.error('mpesa_amount_invalid', amount=amount_kes, error=str(exc))
        raise MpesaValidationError('M-Pesa amount must be a valid number.') from exc

    if amount <= 0:
        raise MpesaValidationError('M-Pesa amount must be greater than zero.')

    normalized_phone = normalize_mpesa_phone(phone_number)
    timestamp = get_mpesa_timestamp()
    token = get_mpesa_access_token()

    payload = {
        'BusinessShortCode': config['shortcode'],
        'Password': build_mpesa_password(config['shortcode'], config['passkey'], timestamp),
        'Timestamp': timestamp,
        'TransactionType': config['transaction_type'],
        'Amount': amount,
        'PartyA': normalized_phone,
        'PartyB': config['shortcode'],
        'PhoneNumber': normalized_phone,
        'CallBackURL': config['callback_url'],
        'AccountReference': order_id or config['account_reference'],
        'TransactionDesc': description[:182],
    }

    try:
        response = requests.post(
            f"{get_mpesa_base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={'Authorization': f"Bearer {token}"},
            timeout=config['timeout_seconds'],
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as exc:
        logger.error('mpesa_stk_timeout', phone_number=normalized_phone, amount=amount, error=str(exc))
        raise MpesaApiError('M-Pesa request timed out. Please try again.') from exc
    except requests.RequestException as exc:
        status = getattr(exc.response, 'status_code', None)
        body = None
        try:
            body = exc.response.json()
        except Exception:
            body = exc.response.text if exc.response is not None else None
        logger.error('mpesa_stk_request_error', status_code=status, response_body=body)
        raise MpesaApiError('M-Pesa service could not process the request. Please try again.') from exc
    except ValueError as exc:
        logger.error('mpesa_stk_parse_error', error=str(exc), response_text=response.text if 'response' in locals() else None)
        raise MpesaApiError('Unexpected response from M-Pesa. Please contact support.') from exc

    if not isinstance(data, dict):
        logger.error('mpesa_stk_invalid_response', response_data=data)
        raise MpesaApiError('Invalid response from M-Pesa. Please contact support.')

    response_code = str(data.get('ResponseCode', '')).strip()
    if response_code not in {'0', '00'}:
        logger.warning('mpesa_stk_error_response', response_code=response_code, response_description=data.get('ResponseDescription'))
        raise MpesaApiError(
            f"M-Pesa declined the request: {data.get('ResponseDescription', 'Unknown error')}"
        )

    return {
        'MerchantRequestID': data.get('MerchantRequestID'),
        'CheckoutRequestID': data.get('CheckoutRequestID'),
        'ResponseCode': response_code,
        'ResponseDescription': data.get('ResponseDescription'),
        'CustomerMessage': data.get('CustomerMessage'),
    }, normalized_phone

def query_mpesa_stk_status(checkout_request_id):
    config = get_mpesa_config()
    if not mpesa_is_configured():
        raise ValueError('M-Pesa is not fully configured.')

    timestamp = get_mpesa_timestamp()
    token = get_mpesa_access_token()
    payload = {
        'BusinessShortCode': config['shortcode'],
        'Password': build_mpesa_password(config['shortcode'], config['passkey'], timestamp),
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }
    response = requests.post(
        f"{get_mpesa_base_url()}/mpesa/stkpushquery/v1/query",
        json=payload,
        headers={'Authorization': f"Bearer {token}"},
        timeout=config['timeout_seconds'],
    )
    response.raise_for_status()
    return response.json()

def extract_mpesa_callback_metadata(callback_metadata):
    items = callback_metadata.get('Item', []) if isinstance(callback_metadata, dict) else []
    metadata = {}
    for item in items:
        name = item.get('Name')
        if name:
            metadata[name] = item.get('Value')
    return metadata
