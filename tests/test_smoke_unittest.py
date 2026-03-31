import unittest
from unittest.mock import patch

import app as app_module
from app.models import AmazonConnection, Invitation, User
from app.services.listing_service import ListingService
from tests.smoke_support import attach_connection, build_test_app, login_test_user


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_test_app()

    def setUp(self):
        self.client = self.app.test_client()
        fake_db = app_module.mongo.db
        for collection_name in ('users', 'amazon_connections', 'update_logs', 'bulk_update_jobs', 'invitations'):
            getattr(fake_db, collection_name).docs = []

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'ok'})

    def test_register_and_login_flow(self):
        response = login_test_user(self.client)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)

    def test_invite_required_after_first_user(self):
        login_test_user(self.client, email='owner@example.com')
        self.client.get('/auth/logout', follow_redirects=True)
        invite = Invitation({'email': 'member@example.com', 'invited_by_user_id': 'owner-id'}).save()

        denied = self.client.post(
            '/auth/register',
            data={
                'name': 'Blocked User',
                'email': 'blocked@example.com',
                'password': 'secret123',
                'confirm_password': 'secret123',
            },
            follow_redirects=True,
        )
        self.assertIn(b'invitation link is required', denied.data)

        allowed = self.client.post(
            '/auth/register',
            data={
                'name': 'Invited User',
                'email': 'member@example.com',
                'password': 'secret123',
                'confirm_password': 'secret123',
                'invite_token': invite.token,
            },
            follow_redirects=True,
        )
        self.assertIn(b'Registration successful', allowed.data)

    def test_amazon_settings_page_renders_for_logged_in_user(self):
        login_test_user(self.client)
        response = self.client.get('/settings/amazon')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Amazon Settings', response.data)

    def test_multiple_accounts_same_marketplace_render_and_selected_connection_is_used(self):
        login_test_user(self.client)
        attach_connection()
        fake_db = app_module.mongo.db
        user = fake_db.users.docs[0]
        app_module.mongo.db.amazon_connections.insert_one({
            'user_id': str(user['_id']),
            'seller_id': 'SELLER-INDIA-2',
            'marketplace_id': 'A21TJRUUN4KGV',
            'marketplace_name': 'India',
            'refresh_token_encrypted': 'encrypted-token-india-2',
            'is_active': True,
            'is_selected': False,
        })
        response = self.client.get('/settings/amazon')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connected Seller Accounts', response.data)
        self.assertIn(b'SELLER123', response.data)
        self.assertIn(b'SELLER-INDIA-2', response.data)

    def test_search_uses_working_account_when_another_account_fails(self):
        login_test_user(self.client)
        user = attach_connection()
        app_module.mongo.db.amazon_connections.insert_one({
            'user_id': user.id,
            'seller_id': 'SELLER-FAIL',
            'marketplace_id': 'A21TJRUUN4KGV',
            'marketplace_name': 'India',
            'refresh_token_encrypted': 'encrypted-token-india-2',
            'is_active': True,
            'is_selected': False,
        })

        with self.app.app_context():
            service = ListingService(User.find_by_email('qa@example.com'))

            class FakeClient:
                def __init__(self, seller_id):
                    self.seller_id = seller_id

                def search_catalog_items(self, keywords=None, identifiers=None, identifier_type='ASIN', page_size=20):
                    if self.seller_id == 'SELLER-FAIL':
                        raise Exception('unauthorized_client')
                    return {
                        'items': [{
                            'asin': 'B0TESTASIN',
                            'summaries': [{'itemName': 'Test Product', 'brandName': 'Brand', 'productType': 'PRODUCT'}],
                            'attributes': {},
                            'images': [],
                        }]
                    }

            service._client_for_connection = lambda connection: FakeClient(connection.seller_id)
            items = service.search_items(asins=['B0TESTASIN'])

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['resolved_connection']['seller_id'], 'SELLER123')

    def test_manual_update_page_renders_for_connected_user(self):
        login_test_user(self.client)
        attach_connection()
        response = self.client.get('/listings/manual-update')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manual Listing Update', response.data)
        self.assertNotIn(b'Inventory Update', response.data)

    def test_bulk_update_page_renders_for_connected_user(self):
        login_test_user(self.client)
        attach_connection()
        response = self.client.get('/listings/bulk-update')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bulk Update', response.data)
        self.assertNotIn(b'Inventory Update', response.data)

    def test_search_route_handles_service_failure_gracefully(self):
        login_test_user(self.client)
        attach_connection()

        def boom(self, keywords=None, asins=None, page_size=20):
            raise Exception('search unavailable')

        with patch.object(ListingService, 'search_items', boom):
            response = self.client.get('/listings/search?type=asin&q=B0TESTASIN')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search failed: search unavailable', response.data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
