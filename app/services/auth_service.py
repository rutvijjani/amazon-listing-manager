"""
Authentication and Token Management Services
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode
from cryptography.fernet import Fernet
from flask import current_app


class TokenEncryption:
    """Encrypt/decrypt sensitive tokens"""
    
    def __init__(self, key=None):
        self.key = key or current_app.config.get('TOKEN_ENCRYPTION_KEY')
        if not self.key:
            # Generate a key if not provided (not recommended for production)
            self.key = Fernet.generate_key().decode()
        self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
    
    def encrypt(self, text):
        """Encrypt text"""
        if not text:
            return None
        encrypted = self.cipher.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text):
        """Decrypt text"""
        if not encrypted_text:
            return None
        try:
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return None


class AmazonOAuth:
    """Login with Amazon OAuth flow handler"""
    
    LWA_ENDPOINT = 'https://api.amazon.com/auth/o2/token'
    AUTHORIZE_ENDPOINT = 'https://www.amazon.com/ap/oa'
    
    # Marketplace IDs
    MARKETPLACES = {
        'A2Q3Y263D00KWC': 'Brazil',
        'A2EUQ1WTGCTBG2': 'Canada', 
        'A1AM78C64UM0Y8': 'Mexico',
        'ATVPDKIKX0DER': 'United States',
        'A2VIGQ35RCS4UG': 'United Arab Emirates',
        'A1PA6795UKMFR9': 'Germany',
        'ARBP9OOSHTCHU': 'Egypt',
        'A1RKKUPIHCS9HS': 'Spain',
        'A13V1IB3VIYZZH': 'France',
        'A1F83G8C2ARO7P': 'United Kingdom',
        'A21TJRUUN4KGV': 'India',  # Default for user
        'APJ6JRA9NG5V4': 'Italy',
        'A1805IZSGTT6HS': 'Netherlands',
        'A17E79C6D8DWNP': 'Poland',
        'A2NODRKZP88ZB9': 'Sweden',
        'A33AVAJ2PDY3EV': 'Turkey',
        'A39IBJ37TRP1C6': 'Australia',
        'A1VC38T7YXB528': 'Japan',
        'A19VAU5U5O7RUS': 'Singapore',
    }

    SELLER_CENTRAL_URLS = {
        'A2Q3Y263D00KWC': 'https://sellercentral.amazon.com.br',
        'A2EUQ1WTGCTBG2': 'https://sellercentral.amazon.ca',
        'A1AM78C64UM0Y8': 'https://sellercentral.amazon.com.mx',
        'ATVPDKIKX0DER': 'https://sellercentral.amazon.com',
        'A2VIGQ35RCS4UG': 'https://sellercentral.amazon.ae',
        'A1PA6795UKMFR9': 'https://sellercentral-europe.amazon.com',
        'ARBP9OOSHTCHU': 'https://sellercentral.amazon.eg',
        'A1RKKUPIHCS9HS': 'https://sellercentral-europe.amazon.com',
        'A13V1IB3VIYZZH': 'https://sellercentral-europe.amazon.com',
        'A1F83G8C2ARO7P': 'https://sellercentral-europe.amazon.com',
        'A21TJRUUN4KGV': 'https://sellercentral.amazon.in',
        'APJ6JRA9NG5V4': 'https://sellercentral-europe.amazon.com',
        'A1805IZSGTT6HS': 'https://sellercentral.amazon.nl',
        'A17E79C6D8DWNP': 'https://sellercentral.amazon.pl',
        'A2NODRKZP88ZB9': 'https://sellercentral.amazon.se',
        'A33AVAJ2PDY3EV': 'https://sellercentral.amazon.com.tr',
        'A39IBJ37TRP1C6': 'https://sellercentral.amazon.com.au',
        'A1VC38T7YXB528': 'https://sellercentral.amazon.co.jp',
        'A19VAU5U5O7RUS': 'https://sellercentral.amazon.sg',
    }
    
    def __init__(self):
        self.application_id = current_app.config.get('SPAPI_APPLICATION_ID')
        self.client_id = current_app.config.get('LWA_CLIENT_ID')
        self.client_secret = current_app.config.get('LWA_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('AMAZON_REDIRECT_URI')
        self.login_uri = current_app.config.get('AMAZON_LOGIN_URI')
        self.auth_version = current_app.config.get('SPAPI_AUTH_VERSION')

    def _validate_token_config(self):
        """Ensure LWA token exchange configuration is present."""
        missing = [
            key for key, value in {
                'LWA_CLIENT_ID': self.client_id,
                'LWA_CLIENT_SECRET': self.client_secret,
                'AMAZON_REDIRECT_URI': self.redirect_uri,
            }.items() if not value
        ]
        if missing:
            raise Exception(f"Missing Amazon OAuth configuration: {', '.join(missing)}")

    def _validate_authorization_config(self):
        """Ensure website authorization workflow configuration is present."""
        missing = [
            key for key, value in {
                'SPAPI_APPLICATION_ID': self.application_id,
                'AMAZON_REDIRECT_URI': self.redirect_uri,
            }.items() if not value
        ]
        if missing:
            raise Exception(f"Missing Amazon authorization configuration: {', '.join(missing)}")
    
    def get_authorization_url(self, state=None, marketplace_id='A21TJRUUN4KGV'):
        """
        Generate Seller Central website authorization URL.
        """
        self._validate_authorization_config()
        seller_central_url = self.get_seller_central_url(marketplace_id)
        params = {'application_id': self.application_id}
        if state:
            params['state'] = state
        if self.auth_version:
            params['version'] = self.auth_version

        return f"{seller_central_url}/apps/authorize/consent?{urlencode(params)}"

    def get_callback_redirect_url(self, amazon_callback_uri, amazon_state, state):
        """Build redirect URL back to Amazon callback URI."""
        self._validate_authorization_config()
        params = {
            'amazon_state': amazon_state,
            'state': state,
            'redirect_uri': self.redirect_uri,
        }
        if self.auth_version:
            params['version'] = self.auth_version
        return f"{amazon_callback_uri}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code):
        """
        Exchange authorization code for access and refresh tokens
        """
        self._validate_token_config()
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
        }
        
        response = requests.post(
            self.LWA_ENDPOINT,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh access token using refresh token
        """
        self._validate_token_config()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        response = requests.post(
            self.LWA_ENDPOINT,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 200:
            result = response.json()
            # Calculate expiry time
            expires_in = result.get('expires_in', 3600)
            expiry_time = datetime.utcnow() + timedelta(seconds=expires_in)
            result['expires_at'] = expiry_time
            return result
        else:
            raise Exception(f"Token refresh failed: {response.text}")
    
    @staticmethod
    def get_marketplace_name(marketplace_id):
        """Get marketplace name from ID"""
        return AmazonOAuth.MARKETPLACES.get(marketplace_id, 'Unknown')
    
    @staticmethod
    def get_sp_api_endpoint(marketplace_id):
        """Get SP-API endpoint for marketplace"""
        # North America
        if marketplace_id in ['ATVPDKIKX0DER', 'A2EUQ1WTGCTBG2', 'A1AM78C64UM0Y8', 'A2Q3Y263D00KWC']:
            return 'https://sellingpartnerapi-na.amazon.com'
        # Europe (including India, UAE, Turkey, Egypt)
        elif marketplace_id in ['A1PA6795UKMFR9', 'ARBP9OOSHTCHU', 'A1RKKUPIHCS9HS', 
                                'A13V1IB3VIYZZH', 'A1F83G8C2ARO7P', 'APJ6JRA9NG5V4',
                                'A1805IZSGTT6HS', 'A17E79C6D8DWNP', 'A2NODRKZP88ZB9',
                                'A2VIGQ35RCS4UG', 'A21TJRUUN4KGV', 'A33AVAJ2PDY3EV']:
            return 'https://sellingpartnerapi-eu.amazon.com'
        # Far East
        elif marketplace_id in ['A39IBJ37TRP1C6', 'A1VC38T7YXB528', 'A19VAU5U5O7RUS']:
            return 'https://sellingpartnerapi-fe.amazon.com'
        # Default to North America
        else:
            return 'https://sellingpartnerapi-na.amazon.com'
    
    @staticmethod
    def get_aws_region_for_marketplace(marketplace_id):
        """Get AWS region for SP-API signing based on marketplace"""
        # North America endpoint → us-east-1
        if marketplace_id in ['ATVPDKIKX0DER', 'A2EUQ1WTGCTBG2', 'A1AM78C64UM0Y8', 'A2Q3Y263D00KWC']:
            return 'us-east-1'
        # Europe endpoint → eu-west-1
        elif marketplace_id in ['A1PA6795UKMFR9', 'ARBP9OOSHTCHU', 'A1RKKUPIHCS9HS', 
                                'A13V1IB3VIYZZH', 'A1F83G8C2ARO7P', 'APJ6JRA9NG5V4',
                                'A1805IZSGTT6HS', 'A17E79C6D8DWNP', 'A2NODRKZP88ZB9',
                                'A2VIGQ35RCS4UG', 'A21TJRUUN4KGV', 'A33AVAJ2PDY3EV']:
            return 'eu-west-1'
        # Far East endpoint → us-west-2
        elif marketplace_id in ['A39IBJ37TRP1C6', 'A1VC38T7YXB528', 'A19VAU5U5O7RUS']:
            return 'us-west-2'
        # Default
        else:
            return 'us-east-1'

    @staticmethod
    def get_seller_central_url(marketplace_id):
        """Get Seller Central URL for the given marketplace."""
        return AmazonOAuth.SELLER_CENTRAL_URLS.get(marketplace_id, 'https://sellercentral.amazon.in')
