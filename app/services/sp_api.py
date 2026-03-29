"""
Amazon Selling Partner API (SP-API) Client
Handles authentication, request signing, and API calls
"""

import requests
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from flask import current_app
from app.services.auth_service import AmazonOAuth, TokenEncryption


class SPAPIClient:
    """
    Amazon Selling Partner API Client
    
    Handles:
    - AWS SigV4 request signing
    - LWA token management
    - API endpoint routing
    """
    
    def __init__(self, connection=None, user=None):
        """
        Initialize SP-API client
        
        Args:
            connection: AmazonConnection model instance
            user: User model instance (alternative to connection)
        """
        self.connection = connection
        self.user = user or (connection.user if connection else None)
        
        # AWS Credentials
        self.aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        self.role_arn = current_app.config.get('SP_API_ROLE_ARN')
        
        # Determine AWS region based on marketplace
        if self.connection:
            marketplace_id = self.connection.marketplace_id or 'A21TJRUUN4KGV'
            self.aws_region = AmazonOAuth.get_aws_region_for_marketplace(marketplace_id)
            current_app.logger.info(f"Marketplace ID from connection: {marketplace_id}")
            current_app.logger.info(f"Resolved AWS region: {self.aws_region}")
        else:
            self.aws_region = current_app.config.get('AWS_REGION', 'us-east-1')
        
        # Token encryption
        self.encryption = TokenEncryption()
        
        # Session credentials (fetched on first use)
        self._session_credentials = None
        self._access_token = None
    
    def _get_access_token(self):
        """Get valid access token (refresh if needed)"""
        if not self.connection:
            raise Exception("No Amazon connection provided")
        
        from app.models import AmazonConnection
        from app import db
        
        # Check if we have a valid cached token
        if self.connection.access_token_encrypted and self.connection.token_expires_at:
            if self.connection.token_expires_at > datetime.utcnow() + timedelta(minutes=5):
                # Token is still valid (with 5 min buffer)
                return self.encryption.decrypt(self.connection.access_token_encrypted)
        
        # Need to refresh token
        oauth = AmazonOAuth()
        refresh_token = self.encryption.decrypt(self.connection.refresh_token_encrypted)
        
        try:
            token_data = oauth.refresh_access_token(refresh_token)
            
            # Update connection with new tokens
            self.connection.access_token_encrypted = self.encryption.encrypt(token_data['access_token'])
            self.connection.token_expires_at = token_data['expires_at']
            self.connection.updated_at = datetime.utcnow()
            db.session.commit()
            
            return token_data['access_token']
        except Exception as e:
            current_app.logger.error(f"Failed to refresh token: {e}")
            raise
    
    def _get_session_credentials(self):
        """Get STS session credentials for SP-API"""
        if self._session_credentials:
            return self._session_credentials
        
        if not self.role_arn:
            # Use static credentials (not recommended for production)
            self._session_credentials = {
                'AccessKeyId': self.aws_access_key,
                'SecretAccessKey': self.aws_secret_key,
                'SessionToken': None
            }
            return self._session_credentials
        
        # Assume role via STS - STS is a global service, use us-east-1 for STS calls
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name='us-east-1'  # STS works globally from us-east-1
        )
        
        try:
            current_app.logger.info(f"Assuming role: {self.role_arn}")
            current_app.logger.info(f"Using AWS region: {self.aws_region}")
            assumed_role = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName='SPAPISession',
                DurationSeconds=3600
            )
            
            self._session_credentials = assumed_role['Credentials']
            current_app.logger.info("Role assumed successfully")
            return self._session_credentials
        except Exception as e:
            current_app.logger.error(f"Failed to assume role: {e}")
            raise
    
    def _make_request(self, method, path, data=None, params=None, content_type='application/json'):
        """
        Make signed request to SP-API
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., '/catalog/2022-04-01/items')
            data: Request body (dict)
            params: Query parameters (dict)
            content_type: Content-Type header
        
        Returns:
            Response JSON dict
        """
        if not self.connection:
            raise Exception("No Amazon connection available")
        
        # Get endpoint
        endpoint = AmazonOAuth.get_sp_api_endpoint(self.connection.marketplace_id)
        url = f"{endpoint}{path}"
        
        # Debug logging
        current_app.logger.info(f"SP-API Request: {method} {url}")
        current_app.logger.info(f"Marketplace: {self.connection.marketplace_id}")
        current_app.logger.info(f"AWS Region for signing: {self.aws_region}")
        
        # Get tokens
        access_token = self._get_access_token()
        credentials = self._get_session_credentials()
        
        # Prepare request body
        body = json.dumps(data) if data else ''
        
        # Create AWS request for signing
        request = AWSRequest(
            method=method,
            url=url,
            data=body,
            headers={
                'host': urlparse(url).netloc,
                'x-amz-access-token': access_token,
                'content-type': content_type,
            }
        )
        
        if params:
            request.params = params
        
        # Sign the request
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials.get('SessionToken'),
            region_name=self.aws_region
        )
        
        sigv4 = SigV4Auth(session.get_credentials(), 'execute-api', self.aws_region)
        sigv4.add_auth(request)
        
        # Prepare headers for requests library
        headers = dict(request.headers)
        headers['x-amz-access-token'] = access_token
        
        # Make the request
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body if body else None,
                params=params,
                timeout=60
            )
            
            # Handle response
            if response.status_code in [200, 201, 202]:
                return response.json() if response.text else {}
            else:
                error_msg = f"SP-API Error {response.status_code}: {response.text}"
                current_app.logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Request failed: {e}")
            raise
    
    # ==================== Catalog API ====================
    
    def search_catalog_items(self, keywords=None, identifiers=None, identifier_type='ASIN', 
                            marketplace_ids=None, page_size=10):
        """
        Search catalog items
        
        Args:
            keywords: Search keywords
            identifiers: List of ASINs or SKUs
            identifier_type: 'ASIN' or 'SellerSKU'
            marketplace_ids: List of marketplace IDs
            page_size: Results per page
        """
        params = {
            'marketplaceIds': ','.join(marketplace_ids or [self.connection.marketplace_id]),
            'pageSize': page_size,
            'includedData': 'summaries,attributes,images,salesRanks'
        }
        
        if keywords:
            params['keywords'] = keywords
        
        if identifiers:
            params['identifiers'] = ','.join(identifiers)
            params['identifiersType'] = identifier_type
        
        return self._make_request('GET', '/catalog/2022-04-01/items', params=params)
    
    def get_catalog_item(self, asin, marketplace_ids=None):
        """
        Get specific catalog item by ASIN
        """
        params = {
            'marketplaceIds': ','.join(marketplace_ids or [self.connection.marketplace_id]),
            'includedData': 'summaries,attributes,images,salesRanks,classifications'
        }
        
        return self._make_request('GET', f'/catalog/2022-04-01/items/{asin}', params=params)
    
    # ==================== Listings Items API ====================
    
    def get_listings_item(self, seller_id, sku, marketplace_ids=None):
        """
        Get listing item by seller SKU
        """
        params = {
            'marketplaceIds': ','.join(marketplace_ids or [self.connection.marketplace_id]),
            'includedData': 'summaries,attributes,issues,offers,fulfillmentAvailability'
        }
        
        return self._make_request(
            'GET', 
            f'/listings/2021-08-01/items/{seller_id}/{sku}',
            params=params
        )
    
    def patch_listings_item(self, seller_id, sku, patches, product_type='PRODUCT'):
        """
        Partial update of listing item (price, quantity, etc.)
        
        Args:
            seller_id: Amazon Seller ID
            sku: Seller SKU
            patches: List of patch operations
            product_type: Product type (default: PRODUCT)
        """
        data = {
            'productType': product_type,
            'patches': patches
        }
        
        return self._make_request(
            'PATCH',
            f'/listings/2021-08-01/items/{seller_id}/{sku}',
            data=data
        )
    
    def put_listings_item(self, seller_id, sku, data):
        """
        Create or fully update a listing item
        """
        return self._make_request(
            'PUT',
            f'/listings/2021-08-01/items/{seller_id}/{sku}',
            data=data
        )
    
    def delete_listings_item(self, seller_id, sku):
        """
        Delete a listing item
        """
        params = {
            'marketplaceIds': self.connection.marketplace_id
        }
        
        return self._make_request(
            'DELETE',
            f'/listings/2021-08-01/items/{seller_id}/{sku}',
            params=params
        )
    
    # ==================== Feeds API ====================
    
    def create_feed_document(self, content_type='application/json'):
        """
        Create feed document for uploading feed data
        """
        data = {
            'contentType': content_type
        }
        
        return self._make_request('POST', '/feeds/2021-06-30/documents', data=data)
    
    def submit_feed(self, feed_type, feed_document_id, marketplace_ids=None):
        """
        Submit feed for processing
        
        Common feed types:
        - JSON_LISTINGS_FEED: For creating/updating listings
        - POST_PRODUCT_DATA: XML product data
        - POST_INVENTORY_AVAILABILITY_DATA: Inventory updates
        - POST_PRODUCT_PRICING_DATA: Pricing updates
        """
        data = {
            'feedType': feed_type,
            'marketplaceIds': marketplace_ids or [self.connection.marketplace_id],
            'inputFeedDocumentId': feed_document_id
        }
        
        return self._make_request('POST', '/feeds/2021-06-30/feeds', data=data)
    
    def get_feed(self, feed_id):
        """Get feed status and details"""
        return self._make_request('GET', f'/feeds/2021-06-30/feeds/{feed_id}')
    
    def get_feed_document(self, feed_document_id):
        """Get feed document (results)"""
        return self._make_request('GET', f'/feeds/2021-06-30/documents/{feed_document_id}')
    
    # ==================== Helper Methods ====================
    
    def update_price(self, seller_id, sku, price, currency='INR', sale_price=None, 
                     sale_start=None, sale_end=None):
        """
        Update product price
        
        Args:
            seller_id: Amazon Seller ID
            sku: Product SKU
            price: Regular price
            currency: Currency code (default: INR)
            sale_price: Optional sale price
            sale_start: Sale start date (ISO format)
            sale_end: Sale end date (ISO format)
        """
        marketplace_id = self.connection.marketplace_id
        
        # Build purchasable offer
        offer = {
            'marketplace_id': marketplace_id,
            'currency': currency,
            'amount': str(price)
        }
        
        patches = [{
            'op': 'replace',
            'path': '/attributes/purchasable_offer',
            'value': [offer]
        }]
        
        # Add sale price if provided
        if sale_price:
            sale_offer = {
                'marketplace_id': marketplace_id,
                'currency': currency,
                'amount': str(sale_price)
            }
            patches.append({
                'op': 'replace',
                'path': '/attributes/sale',
                'value': [{
                    'start_at': sale_start or datetime.utcnow().isoformat(),
                    'end_at': sale_end or (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'sale_price': [sale_offer]
                }]
            })
        
        return self.patch_listings_item(seller_id, sku, patches)
    
    def update_inventory(self, seller_id, sku, quantity, fulfillment_channel='DEFAULT'):
        """
        Update inventory quantity
        
        Args:
            seller_id: Amazon Seller ID
            sku: Product SKU
            quantity: Available quantity
            fulfillment_channel: 'DEFAULT' (FBM) or 'AMAZON' (FBA)
        """
        patches = [{
            'op': 'replace',
            'path': '/attributes/fulfillment_availability',
            'value': [{
                'fulfillment_channel_code': fulfillment_channel,
                'quantity': quantity
            }]
        }]
        
        return self.patch_listings_item(seller_id, sku, patches)
