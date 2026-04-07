import os
import bcrypt
from datetime import timedelta
from ..extensions import db
from ..models import User, Product, Promotion, SiteContent
from .helpers import (
    calculate_prices, 
    now_utc, 
    validate_promotion_payload, 
    apply_promotion_model_updates, 
    sync_promotion_targets
)

def seed_data():
    # 1. Site Content Seeding
    if not SiteContent.query.filter_by(key='hero_title').first():
        db.session.add(SiteContent(key='hero_title', value='Dark Spots & Uneven Tone Stealing Your Glow?'))
        db.session.add(SiteContent(key='hero_subtitle', value='Naturally brighten with toxin-free, melanin-safe luxury skincare.'))
        db.session.commit()

    # 2. Product Catalog Seeding
    product_catalog = [
        {
            'name': 'MELANIN-GLOW Mask',
            'description': 'Advanced brightening clay mask for radiant skin.',
            'base_price_usd': 25.0,
            'category': 'mask',
            'image_url': 'https://queenkoba.com/mask.jpg',
        },
        {
            'name': 'HYDRA-GLOW Serum',
            'description': 'Intense hydration serum with Vitamin C.',
            'base_price_usd': 35.0,
            'category': 'serum',
            'image_url': 'https://queenkoba.com/serum.jpg',
        }
    ]

    for item in product_catalog:
        product = Product.query.filter_by(category=item['category']).first()
        if not product:
            product = Product(
                name=item['name'],
                description=item['description'],
                base_price_usd=item['base_price_usd'],
                category=item['category'],
                in_stock=True,
                image_url=item['image_url'],
                prices=calculate_prices(item['base_price_usd'])
            )
            db.session.add(product)
    
    db.session.commit()

    # 3. Admin User Seeding
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@queenkoba.com')
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='admin',
            email=admin_email,
            password_hash=bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8'),
            role='admin',
            permissions=['*']
        )
        db.session.add(admin)
        db.session.commit()

    # 4. Promotion Seeding
    admin_user = User.query.filter_by(email=admin_email).first()
    seeded_promotions = [
        {
            'code': 'WELCOME10',
            'discount': 10,
            'type': 'percentage',
            'status': 'active',
            'starts_at': now_utc() - timedelta(days=1),
            'expires': now_utc() + timedelta(days=180),
        }
    ]

    for seeded in seeded_promotions:
        promo = Promotion.query.filter_by(code=seeded['code']).first()
        if not promo:
            payload = validate_promotion_payload(seeded)
            promo = Promotion(created_by_admin_id=admin_user.id if admin_user else None)
            db.session.add(promo)
            db.session.flush()
            apply_promotion_model_updates(promo, payload, admin_user_id=admin_user.id if admin_user else None)
            sync_promotion_targets(promo, payload)

    db.session.commit()
