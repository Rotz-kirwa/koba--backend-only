import os
import uuid
import sentry_sdk
from flask import Flask, request, g, jsonify
from sentry_sdk.integrations.flask import FlaskIntegration
import structlog

from .config import Config
from .extensions import db, jwt, cors
from .utils.seed import seed_data

def create_app(config_class=Config):
    # Initialize Sentry
    if config_class.SENTRY_DSN:
        sentry_sdk.init(
            dsn=config_class.SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            environment=config_class.FLASK_ENV
        )

    # Initialize Structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": config_class.ALLOWED_ORIGINS}})

    # Request Trace ID middleware
    @app.before_request
    def before_request():
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
            
        g.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=g.request_id,
            path=request.path,
            method=request.method,
            client_ip=request.remote_addr
        )

    # Database Initialization Hook
    @app.before_request
    def initialize_database():
        if not hasattr(app, 'db_initialized'):
            with app.app_context():
                db.create_all()
                seed_data()
                app.db_initialized = True

    # Register Blueprints (will be populated in next steps)
    from .routes.auth import auth_bp
    from .routes.products import products_bp
    from .routes.cart import cart_bp
    from .routes.checkout import checkout_bp
    from .routes.payments import payments_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(checkout_bp, url_prefix='/api/checkout')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app
