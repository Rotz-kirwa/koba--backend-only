import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Environment & Secrets
    SECRET_KEY = os.getenv('SECRET_KEY', 'queenkoba-flash-secret')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    
    # SQLAlchemy Configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///queenkoba.db')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 20,
        "max_overflow": 40,
        "pool_recycle": 1800,
        "pool_timeout": 30,
        "pool_pre_ping": True,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'queenkoba-super-secret-jwt-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Sentry Configuration
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    
    # CORS Configuration
    ALLOWED_ORIGINS = [
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        os.getenv('FRONTEND_URL', ''),
        os.getenv('ADMIN_URL', ''),
    ]
    
    _extra_origins = os.getenv('CORS_ORIGINS', '')
    if _extra_origins:
        # Standardize formatting to avoid duplicates or junk entries
        _origins_split = [o.strip() for o in _extra_origins.split(",") if o.strip()]
        ALLOWED_ORIGINS.extend(_origins_split)
    
    # Filter empty origins and remove duplicates
    ALLOWED_ORIGINS = list(set([o for o in ALLOWED_ORIGINS if o]))

    # Google Auth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '445338583811-0gknu3ni8fn9mh3pa874agtu61i29tvr.apps.googleusercontent.com')