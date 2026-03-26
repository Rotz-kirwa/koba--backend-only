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


if __name__ == "__main__":
    unittest.main()
