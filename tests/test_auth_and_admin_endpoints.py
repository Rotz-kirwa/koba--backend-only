import os
import sys
import unittest
from pathlib import Path


TEST_DB_PATH = Path(__file__).with_name("test_backend_suite.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-auth-admin-secret-32-bytes"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import queenkoba_postgresql as backend  # noqa: E402


class AuthAndAdminEndpointTests(unittest.TestCase):
    legacy_counter = 0
    customer_counter = 0

    @classmethod
    def setUpClass(cls):
        backend.app.config["TESTING"] = True
        backend.app.db_initialized = True
        cls.client = backend.app.test_client()

    def setUp(self):
        with backend.app.app_context():
            backend.db.drop_all()
            backend.db.create_all()
            backend.ensure_schema_updates()
            backend.seed_data()

        with backend.app.app_context():
            admin = backend.User.query.filter_by(email="admin@queenkoba.com").first()
            self.admin_token = backend.create_access_token(identity=str(admin.id))

    def _admin_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}"}

    def _create_customer(self):
        AuthAndAdminEndpointTests.customer_counter += 1
        email = f"admin-order-customer-{AuthAndAdminEndpointTests.customer_counter}@example.com"

        with backend.app.app_context():
            user = backend.User(
                username=f"ordercustomer{AuthAndAdminEndpointTests.customer_counter}",
                name="Admin Order Customer",
                email=email,
                phone="0712345678",
                password_hash=backend.bcrypt.hashpw(b"1234", backend.bcrypt.gensalt()).decode("utf-8"),
                role="customer",
                country="Kenya",
                preferred_currency="KES",
            )
            backend.db.session.add(user)
            backend.db.session.commit()
            return user.id, email

    def _customer_headers(self, user_id):
        with backend.app.app_context():
            token = backend.create_access_token(identity=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    def _catalog_item(self, category, quantity=1):
        with backend.app.app_context():
            product = backend.Product.query.filter_by(category=category).first()
            self.assertIsNotNone(product)
            order_item = backend.build_order_item_payload(product, quantity)
            return {
                "product_id": order_item["product_id"],
                "product_name": order_item["product_name"],
                "quantity": quantity,
                "price_per_item_kes": order_item["price_per_item_kes"],
                "item_total_kes": order_item["item_total_kes"],
            }

    def test_signup_rejects_weak_pin_password(self):
        response = self.client.post(
            "/auth/signup",
            json={
                "name": "Weak Password Customer",
                "email": "weak-password@example.com",
                "phone": "0712345678",
                "password": "1234",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 8 characters", response.get_json()["message"].lower())

    def test_login_accepts_existing_legacy_customer_password(self):
        AuthAndAdminEndpointTests.legacy_counter += 1
        email = f"legacy-customer-{AuthAndAdminEndpointTests.legacy_counter}@example.com"

        with backend.app.app_context():
            user = backend.User(
                username="legacycustomer",
                name="Legacy Customer",
                email=email,
                phone="0712345678",
                password_hash=backend.bcrypt.hashpw(b"1234", backend.bcrypt.gensalt()).decode("utf-8"),
                role="customer",
                country="Kenya",
                preferred_currency="KES",
            )
            backend.db.session.add(user)
            backend.db.session.commit()

        response = self.client.post(
            "/auth/login",
            json={"email": email, "password": "1234"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["user"]["email"], email)
        self.assertTrue(payload.get("token"))

    def test_admin_auth_me_returns_current_admin(self):
        response = self.client.get("/admin/auth/me", headers=self._admin_headers())

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["user"]["email"], "admin@queenkoba.com")
        self.assertEqual(payload["user"]["status"], "active")

    def test_admin_analytics_overview_returns_expected_shape(self):
        response = self.client.get("/admin/analytics/overview", headers=self._admin_headers())

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        analytics = payload["analytics"]
        self.assertEqual(len(analytics["monthly"]), 6)
        self.assertIn("summary", analytics)
        self.assertIn("top_products", analytics)

    def test_public_products_and_content_support_lite_mode(self):
        products_response = self.client.get("/products?lite=true&limit=3")
        self.assertEqual(products_response.status_code, 200)
        products_payload = products_response.get_json()
        self.assertTrue(products_payload["lite"])
        self.assertLessEqual(products_payload["count"], 3)
        self.assertTrue(products_payload["products"])
        self.assertNotIn("base_price_usd", products_payload["products"][0])

        content_response = self.client.get("/content?lite=true")
        self.assertEqual(content_response.status_code, 200)
        content_payload = content_response.get_json()
        self.assertTrue(content_payload["lite"])
        self.assertIn("hero_title", content_payload["content"])
        self.assertIn("footer_text", content_payload["content"])

    def test_admin_can_create_and_update_promotions_with_restrictions(self):
        with backend.app.app_context():
            product = backend.Product.query.first()
            self.assertIsNotNone(product)

        create_response = self.client.post(
            "/admin/promotions",
            json={
                "code": "SPRING15",
                "description": "Spring glow offer",
                "campaign_type": "seasonal",
                "discount_type": "percentage",
                "discount_value": 15,
                "is_active": True,
                "applies_to_type": "products",
                "product_ids": [product.id],
                "usage_limit": 50,
                "per_user_limit": 1,
                "min_order_amount": 3000,
            },
            headers=self._admin_headers(),
        )

        self.assertEqual(create_response.status_code, 201)
        created = create_response.get_json()["promotion"]
        self.assertEqual(created["code"], "SPRING15")
        self.assertEqual(created["applies_to_type"], "products")
        self.assertEqual(created["product_ids"], [product.id])

        update_response = self.client.put(
            f"/admin/promotions/{created['_id']}",
            json={
                "code": "SPRING15",
                "description": "Spring glow offer updated",
                "campaign_type": "seasonal",
                "discount_type": "fixed",
                "discount_value": 500,
                "is_active": False,
                "applies_to_type": "categories",
                "categories": ["serum"],
                "usage_limit": 25,
                "per_user_limit": 2,
                "min_order_amount": 2500,
            },
            headers=self._admin_headers(),
        )

        self.assertEqual(update_response.status_code, 200)
        updated = update_response.get_json()["promotion"]
        self.assertEqual(updated["description"], "Spring glow offer updated")
        self.assertEqual(updated["discount_type"], "fixed")
        self.assertEqual(updated["status"], "inactive")
        self.assertEqual(updated["applies_to_type"], "categories")
        self.assertEqual(updated["categories"], ["serum"])

    def test_paid_mpesa_order_appears_in_admin_with_full_delivery_and_payment_details(self):
        customer_id, customer_email = self._create_customer()
        customer_headers = self._customer_headers(customer_id)
        serum_item = self._catalog_item("Serum", quantity=2)

        original_start_mpesa_stk_push = backend.start_mpesa_stk_push

        def fake_start_mpesa_stk_push(phone_number, amount_kes, order, description='Queen Koba order payment'):
            return (
                {
                    "MerchantRequestID": "MR-123",
                    "CheckoutRequestID": "CHK-123",
                    "CustomerMessage": "STK sent",
                    "ResponseCode": "0",
                    "ResponseDescription": "Success",
                },
                "254712345678",
            )

        backend.start_mpesa_stk_push = fake_start_mpesa_stk_push

        try:
            checkout_response = self.client.post(
                "/checkout",
                json={
                    "items": [serum_item],
                    "totals": {
                        "currency": "KES",
                        "subtotal_kes": serum_item["item_total_kes"],
                        "shipping_kes": 300,
                        "grand_total_kes": serum_item["item_total_kes"] + 300,
                    },
                    "shipping_address": {
                        "name": "Admin Order Customer",
                        "email": customer_email,
                        "phone": "0712345678",
                        "address": "Westlands, Sarit Centre stage",
                        "city": "Nairobi",
                        "country": "Kenya",
                        "county": "Nairobi",
                        "area": "Westlands",
                        "delivery_zone": "Within Nairobi",
                        "delivery_zone_code": "nairobi",
                        "delivery_point": "Sarit Centre stage",
                        "delivery_method": "door",
                    },
                    "payment_method": "mpesa",
                    "payment_details": {
                        "type": "mobile",
                        "phone_number": "0712345678",
                    },
                    "delivery": {
                        "delivery_zone": "Within Nairobi",
                        "delivery_zone_code": "nairobi",
                        "county": "Nairobi",
                        "area": "Westlands",
                        "point": "Sarit Centre stage",
                        "delivery_point": "Sarit Centre stage",
                        "method": "door",
                        "shipping_fee": 300,
                        "eta": "Same day / next day",
                    },
                },
                headers=customer_headers,
            )

            self.assertEqual(checkout_response.status_code, 200)
            order_id = checkout_response.get_json()["order_id"]

            callback_response = self.client.post(
                "/payments/mpesa/callback",
                json={
                    "Body": {
                        "stkCallback": {
                            "CheckoutRequestID": "CHK-123",
                            "ResultCode": 0,
                            "ResultDesc": "The service request is processed successfully.",
                            "CallbackMetadata": {
                                "Item": [
                                    {"Name": "Amount", "Value": float(serum_item["item_total_kes"]) + 300},
                                    {"Name": "MpesaReceiptNumber", "Value": "QK12345678"},
                                    {"Name": "TransactionDate", "Value": 20260327103045},
                                    {"Name": "PhoneNumber", "Value": 254712345678},
                                ]
                            },
                        }
                    }
                },
            )
            self.assertEqual(callback_response.status_code, 200)

            admin_orders_response = self.client.get(
                "/admin/orders?payment_status=paid&search=QK12345678",
                headers=self._admin_headers(),
            )

            self.assertEqual(admin_orders_response.status_code, 200)
            orders = admin_orders_response.get_json()["orders"]
            self.assertEqual(len(orders), 1)
            order = orders[0]

            self.assertEqual(order["order_id"], order_id)
            self.assertEqual(order["payment_status"], "paid")
            self.assertEqual(order["payment_reference"], "QK12345678")
            self.assertEqual(order["payment_method"], "mpesa")
            self.assertEqual(order["customer_name"], "Admin Order Customer")
            self.assertEqual(order["customer_email"], customer_email)
            self.assertEqual(order["customer_phone"], "0712345678")
            self.assertEqual(order["delivery_zone"], "Within Nairobi")
            self.assertEqual(order["county"], "Nairobi")
            self.assertEqual(order["area"], "Westlands")
            self.assertEqual(order["delivery_point"], "Sarit Centre stage")
            self.assertEqual(order["delivery_method"], "door")
            self.assertEqual(order["shipping_kes"], 300.0)
            self.assertEqual(order["payment_phone"], "254712345678")
            self.assertEqual(order["items"][0]["product_name"], serum_item["product_name"])
            self.assertEqual(order["items"][0]["quantity"], 2)
            self.assertTrue(order["paid_at"])
            self.assertEqual(order["shipping_address"]["delivery_point"], "Sarit Centre stage")
        finally:
            backend.start_mpesa_stk_push = original_start_mpesa_stk_push


if __name__ == "__main__":
    unittest.main()
