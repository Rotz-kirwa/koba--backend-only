# Google OAuth Setup Guide

## Overview
The Queen Koba frontend includes Google OAuth integration for easy user authentication.

## Current Status
- ✅ Frontend UI implemented with Google sign-in button
- ✅ Auth context and state management ready
- ⚠️ Backend Google OAuth needs configuration

## To Enable Google OAuth:

### 1. Get Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set authorized redirect URIs:
   - `http://localhost:5000/auth/google/callback`
   - `http://localhost:8080/auth/callback`

### 2. Backend Setup (Python/Flask)
Install required package:
```bash
pip install authlib
```

Add to `.env`:
```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

### 3. Update Backend Code
Replace the placeholder `/auth/google` endpoint in `queenkoba_mongodb.py` with:

```python
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/auth/google')
def google_login():
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    # Check if user exists
    user = mongo.db.users.find_one({'email': user_info['email']})
    
    if not user:
        # Create new user
        user = {
            'name': user_info['name'],
            'email': user_info['email'],
            'role': 'customer',
            'auth_provider': 'google',
            'created_at': datetime.utcnow()
        }
        result = mongo.db.users.insert_one(user)
        user_id = str(result.inserted_id)
    else:
        user_id = str(user['_id'])
    
    # Create JWT token
    access_token = create_access_token(identity=user_id)
    
    # Redirect to frontend with token
    frontend_url = 'http://localhost:8080/auth/callback'
    user_data = {
        'id': user_id,
        'name': user_info['name'],
        'email': user_info['email']
    }
    return redirect(f"{frontend_url}?token={access_token}&user={quote(json.dumps(user_data))}")
```

## Testing
1. Start backend: `python queenkoba_mongodb.py`
2. Start frontend: `npm run dev`
3. Click "Sign in with Google" button
4. Complete Google authentication
5. User should be redirected back and logged in

## Security Notes
- Never commit `.env` file with credentials
- Use HTTPS in production
- Update redirect URIs for production domain
- Implement CSRF protection for production
