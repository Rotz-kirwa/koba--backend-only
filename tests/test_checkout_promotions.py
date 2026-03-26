import os
import sys
import unittest
from pathlib import Path


TEST_DB_PATH = Path(__file__).with_name("test_backend_suite.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-checkout-promotions-secret-32-bytes"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import queenkoba_postgresql as backend  # noqa: E402


class CheckoutPromotionTests(unittest.TestCase):
    user_counter = 0

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

        self.user_id = self._create_customer()
        self.token = self._make_token(self.user_id)

    def _create_customer(self):
        CheckoutPromotionTests.user_counter += 1
        email = f"promo-customer-{CheckoutPromotionTests.user_counter}@example.com"

        with backend.app.app_context():
            user = backend.User(
                username=f"customer{CheckoutPromotionTests.user_counter}",
                name="Promo Test Customer",
                email=email,
                password_hash=backend.bcrypt.hashpw(b"1234", backend.bcrypt.gensalt()).decode("utf-8"),
                role="customer",
                country="Kenya",
                preferred_currency="KES",
            )
            backend.db.session.add(user)
            backend.db.session.commit()
            return user.id

    def _make_token(self, user_id):
        with backend.app.app_context():
            return backend.create_access_token(identity=str(user_id))

    def _auth_headers(self, token=None):
        return {"Authorization": f"Bearer {token or self.token}"}

    def _catalog_item(self, category, quantity=1):
        with backend.app.app_context():
            product = backend.Product.query.filter_by(category=category).first()
            self.assertIsNotNone(product, f"Expected a seeded product for category {category}")
            order_item = backend.build_order_item_payload(product, quantity)
            request_item = {
                "product_id": order_item["product_id"],
                "product_name": order_item["product_name"],
                "quantity": quantity,
                "price_per_item_kes": order_item["price_per_item_kes"],
                "item_total_kes": order_item["item_total_kes"],
            }
            return request_item, float(order_item["item_total_kes"])

    def _checkout_payload(
        self,
        items,
        shipping_fee,
        promo_code=None,
        *,
        delivery_zone="nairobi",
        county="Nairobi",
        area="CBD",
        delivery_point="Kencom stage",
    ):
        delivery_zone_label = "Within Nairobi" if delivery_zone == "nairobi" else "Outside Nairobi"
        return {
            "items": items,
            "totals": {
                "currency": "KES",
                "subtotal_kes": sum(float(item["item_total_kes"]) for item in items),
                "shipping_kes": shipping_fee,
            },
            "promo_code": promo_code,
            "shipping_address": {
                "name": "Promo Test Customer",
                "email": "promo-test@example.com",
                "phone": "254700000000",
                "address": "Nairobi CBD",
                "city": "Nairobi",
                "postal_code": "00100",
                "country": "Kenya",
                "county": county,
                "area": area,
                "delivery_zone": delivery_zone_label,
                "delivery_zone_code": delivery_zone,
                "delivery_point": delivery_point,
            },
            "payment_method": "card",
            "payment_details": {"type": "card"},
            "delivery": {
                "delivery_zone": delivery_zone_label,
                "delivery_zone_code": delivery_zone,
                "county": county,
                "area": area,
                "point": delivery_point,
                "delivery_point": delivery_point,
                "method": "pickup",
                "shipping_fee": shipping_fee,
                "eta": "1-2 days",
            },
        }

    def test_welcome10_preview_matches_checkout_and_records_usage(self):
        serum_item, serum_subtotal = self._catalog_item("Serum")

        preview_response = self.client.post(
            "/cart/apply-promocode",
            json={
                "code": "WELCOME10",
                "items": [{"product_id": serum_item["product_id"], "quantity": serum_item["quantity"]}],
                "shipping_kes": 300,
            },
            headers=self._auth_headers(),
        )
        self.assertEqual(preview_response.status_code, 200)
        preview_promo = preview_response.get_json()["promo"]

        checkout_response = self.client.post(
            "/checkout",
            json=self._checkout_payload([serum_item], shipping_fee=300, promo_code="WELCOME10"),
            headers=self._auth_headers(),
        )
        self.assertEqual(checkout_response.status_code, 200)
        checkout_data = checkout_response.get_json()
        checkout_promo = checkout_data["promo"]

        expected_discount = round(serum_subtotal * 0.10, 2)
        expected_total = round(serum_subtotal + 300 - expected_discount, 2)

        self.assertAlmostEqual(preview_promo["discount_amount"], expected_discount)
        self.assertAlmostEqual(checkout_promo["discount_amount"], expected_discount)
        self.assertAlmostEqual(checkout_promo["final_total_kes"], expected_total)
        self.assertEqual(checkout_promo["promo_code"], "WELCOME10")

        with backend.app.app_context():
            order = backend.Order.query.filter_by(order_id=checkout_data["order_id"]).first()
            promo = backend.Promotion.query.filter_by(code="WELCOME10").first()
            usage = backend.PromotionUsage.query.filter_by(order_id=order.id).first()
            state = backend.get_order_payment_state(order)

            self.assertIsNotNone(order)
            self.assertEqual(order.promo_code, "WELCOME10")
            self.assertAlmostEqual(float(order.discount_amount or 0), expected_discount)
            self.assertAlmostEqual(float(order.final_total_after_discount or 0), expected_total)
            self.assertEqual(int(promo.uses or 0), 1)
            self.assertIsNotNone(usage)
            self.assertEqual(float((state.get("totals") or {}).get("discount_percent", 0) or 0), 10.0)

    def test_validate_endpoint_returns_structured_success_payload(self):
        serum_item, serum_subtotal = self._catalog_item("Serum")

        response = self.client.post(
            "/promotions/validate",
            json={
                "code": "WELCOME10",
                "items": [{"product_id": serum_item["product_id"], "quantity": serum_item["quantity"]}],
                "shipping_kes": 300,
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertTrue(payload["exists"])
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["promo_code"], "WELCOME10")
        self.assertEqual(payload["discount_type"], "percentage")
        self.assertAlmostEqual(payload["applied_discount_amount"], round(serum_subtotal * 0.10, 2))
        self.assertAlmostEqual(
            payload["updated_total"],
            round(serum_subtotal + 300 - (serum_subtotal * 0.10), 2),
        )
        self.assertIsNotNone(payload["promo"])

    def test_validate_endpoint_returns_not_found_and_expired_reasons(self):
        serum_item, _ = self._catalog_item("Serum")

        not_found_response = self.client.post(
            "/promotions/validate",
            json={
                "code": "DOESNOTEXIST",
                "items": [{"product_id": serum_item["product_id"], "quantity": serum_item["quantity"]}],
                "shipping_kes": 300,
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(not_found_response.status_code, 200)
        not_found_payload = not_found_response.get_json()
        self.assertFalse(not_found_payload["exists"])
        self.assertFalse(not_found_payload["valid"])
        self.assertEqual(not_found_payload["reason"], "not_found")
        self.assertIn("not found", not_found_payload["message"].lower())

        with backend.app.app_context():
            promo = backend.Promotion.query.filter_by(code="WELCOME10").first()
            promo.expires = backend.now_utc() - backend.timedelta(days=1)
            backend.db.session.commit()

        expired_response = self.client.post(
            "/promotions/validate",
            json={
                "code": "WELCOME10",
                "items": [{"product_id": serum_item["product_id"], "quantity": serum_item["quantity"]}],
                "shipping_kes": 300,
            },
            headers=self._auth_headers(),
        )

        self.assertEqual(expired_response.status_code, 200)
        expired_payload = expired_response.get_json()
        self.assertTrue(expired_payload["exists"])
        self.assertFalse(expired_payload["valid"])
        self.assertEqual(expired_payload["reason"], "expired")
        self.assertIn("expired", expired_payload["message"].lower())

    def test_welcome10_is_rejected_after_first_successful_order(self):
        serum_item, _ = self._catalog_item("Serum")

        first_response = self.client.post(
            "/checkout",
            json=self._checkout_payload([serum_item], shipping_fee=300, promo_code="WELCOME10"),
            headers=self._auth_headers(),
        )
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            "/checkout",
            json=self._checkout_payload([serum_item], shipping_fee=300, promo_code="WELCOME10"),
            headers=self._auth_headers(),
        )
        self.assertEqual(second_response.status_code, 400)
        self.assertIn("first order", second_response.get_json()["message"].lower())

    def test_freedelivery_removes_shipping_charge_at_checkout(self):
        bundle_item, bundle_subtotal = self._catalog_item("Bundle")

        response = self.client.post(
            "/checkout",
            json=self._checkout_payload(
                [bundle_item],
                shipping_fee=450,
                promo_code="FREEDELIVERY",
                delivery_zone="outside_nairobi",
                county="Nakuru",
                area="Nakuru Town",
                delivery_point="Stage ya posta",
            ),
            headers=self._auth_headers(),
        )
        self.assertEqual(response.status_code, 200)
        promo = response.get_json()["promo"]

        self.assertEqual(promo["promo_code"], "FREEDELIVERY")
        self.assertAlmostEqual(promo["discount_amount"], 0)
        self.assertAlmostEqual(promo["shipping_discount"], 500)
        self.assertAlmostEqual(promo["final_total_kes"], bundle_subtotal)

    def test_outside_nairobi_shipping_is_recalculated_server_side(self):
        serum_item, serum_subtotal = self._catalog_item("Serum")

        response = self.client.post(
            "/checkout",
            json=self._checkout_payload(
                [serum_item],
                shipping_fee=0,
                delivery_zone="outside_nairobi",
                county="Nakuru",
                area="Nakuru Town",
                delivery_point="Stage ya posta",
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        promo = response.get_json()["promo"]
        self.assertAlmostEqual(promo["shipping_kes"], 500)
        self.assertAlmostEqual(promo["final_total_kes"], round(serum_subtotal + 500, 2))

        with backend.app.app_context():
            order = backend.Order.query.filter_by(order_id=response.get_json()["order_id"]).first()
            self.assertIsNotNone(order)
            self.assertEqual((order.shipping_address or {}).get("delivery_zone_code"), "outside_nairobi")
            self.assertEqual((order.shipping_address or {}).get("county"), "Nakuru")
            self.assertEqual((order.shipping_address or {}).get("area"), "Nakuru Town")

    def test_nairobi_like_county_values_still_use_nairobi_shipping_rate(self):
        serum_item, serum_subtotal = self._catalog_item("Serum")

        response = self.client.post(
            "/checkout",
            json=self._checkout_payload(
                [serum_item],
                shipping_fee=500,
                county="Nairobi County",
                area="Westlands",
                delivery_point="Sarit Centre stage",
            ),
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 200)
        promo = response.get_json()["promo"]
        self.assertAlmostEqual(promo["shipping_kes"], 300)
        self.assertAlmostEqual(promo["final_total_kes"], round(serum_subtotal + 300, 2))

    def test_checkout_rejects_missing_structured_delivery_fields(self):
        serum_item, _ = self._catalog_item("Serum")
        payload = self._checkout_payload([serum_item], shipping_fee=300)
        payload["delivery"]["county"] = ""
        payload["shipping_address"]["county"] = ""

        response = self.client.post(
            "/checkout",
            json=payload,
            headers=self._auth_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("county is required", response.get_json()["message"].lower())

    def test_melanin15_only_applies_to_eligible_categories(self):
        cleanser_item, _ = self._catalog_item("Cleanser", quantity=2)

        invalid_response = self.client.post(
            "/checkout",
            json=self._checkout_payload([cleanser_item], shipping_fee=300, promo_code="MELANIN15"),
            headers=self._auth_headers(),
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertIn("does not apply", invalid_response.get_json()["message"].lower())

        serum_item, serum_subtotal = self._catalog_item("Serum")
        valid_response = self.client.post(
            "/checkout",
            json=self._checkout_payload([serum_item], shipping_fee=300, promo_code="MELANIN15"),
            headers=self._auth_headers(),
        )
        self.assertEqual(valid_response.status_code, 200)

        promo = valid_response.get_json()["promo"]
        expected_discount = round(serum_subtotal * 0.15, 2)
        expected_total = round(serum_subtotal + 300 - expected_discount, 2)

        self.assertAlmostEqual(promo["discount_amount"], expected_discount)
        self.assertAlmostEqual(promo["shipping_discount"], 0)
        self.assertAlmostEqual(promo["final_total_kes"], expected_total)


if __name__ == "__main__":
    unittest.main()
