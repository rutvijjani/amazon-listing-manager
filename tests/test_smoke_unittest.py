import unittest
from unittest.mock import patch

from app.services.listing_service import ListingService
from tests.smoke_support import attach_connection, build_test_app, login_test_user


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_test_app()

    def setUp(self):
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_register_and_login_flow(self):
        response = login_test_user(self.client)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)

    def test_amazon_settings_page_renders_for_logged_in_user(self):
        login_test_user(self.client)
        response = self.client.get("/settings/amazon")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Amazon Settings", response.data)

    def test_manual_update_page_renders_for_connected_user(self):
        login_test_user(self.client)
        attach_connection()
        response = self.client.get("/listings/manual-update")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manual Listing Update", response.data)

    def test_bulk_update_page_renders_for_connected_user(self):
        login_test_user(self.client)
        attach_connection()
        response = self.client.get("/listings/bulk-update")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bulk Update", response.data)

    def test_search_route_handles_service_failure_gracefully(self):
        login_test_user(self.client)
        attach_connection()

        def boom(self, keywords=None, asins=None, page_size=20):
            raise Exception("search unavailable")

        with patch.object(ListingService, "search_items", boom):
            response = self.client.get("/listings/search?type=asin&q=B0TESTASIN")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Search failed: search unavailable", response.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
