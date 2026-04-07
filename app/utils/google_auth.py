import os
import requests
from ..models import User
from .mpesa import logger # Reusing the logger from mpesa for consistency or imports

DEFAULT_GOOGLE_CLIENT_ID = '445338583811-0gknu3ni8fn9mh3pa874agtu61i29tvr.apps.googleusercontent.com'

def get_google_client_ids():
    raw_values = []
    for env_name in ('GOOGLE_CLIENT_IDS', 'GOOGLE_CLIENT_ID'):
        raw = os.getenv(env_name, '')
        if raw:
            raw_values.extend(raw.split(','))
    client_ids = [value.strip() for value in raw_values if value.strip()]
    if not client_ids:
        client_ids = [DEFAULT_GOOGLE_CLIENT_ID]
    return list(dict.fromkeys(client_ids))

def get_google_allowed_admin_emails():
    raw_values = []
    for env_name in ('GOOGLE_ALLOWED_EMAILS', 'ADMIN_GOOGLE_EMAILS', 'GOOGLE_ADMIN_EMAILS'):
        raw = os.getenv(env_name, '')
        if raw:
            raw_values.extend(raw.split(','))
    return [value.strip().lower() for value in raw_values if value.strip()]

def verify_google_credential(credential):
    if not credential:
        raise ValueError('Google credential is required')
    try:
        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=10,
        )
        payload = response.json()
    except requests.RequestException:
        raise ValueError('Could not verify Google sign-in right now')
    
    if response.status_code != 200:
        detail = payload.get('error_description') or payload.get('error') or 'Invalid Google credential'
        raise ValueError(detail)

    audience = (payload.get('aud') or '').strip()
    if audience not in get_google_client_ids():
        raise ValueError('Google sign-in does not match the configured client')

    email = (payload.get('email') or '').strip().lower()
    if not email:
        raise ValueError('Google sign-in did not return an email address')

    if str(payload.get('email_verified')).lower() != 'true':
        raise ValueError('A verified Google email is required to continue')

    return {
        'email': email,
        'name': (payload.get('name') or '').strip(),
        'given_name': (payload.get('given_name') or '').strip(),
        'sub': (payload.get('sub') or '').strip(),
    }
