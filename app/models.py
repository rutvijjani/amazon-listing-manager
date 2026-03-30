"""
MongoDB Models for Amazon Listing Manager
"""

import secrets
from datetime import datetime, timedelta, UTC

from bson.objectid import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import mongo


class User(UserMixin):
    """User model for MongoDB"""
    
    collection_name = 'users'
    
    def __init__(self, user_data):
        if user_data is None:
            user_data = {}
        self._id = user_data.get('_id')
        self.email = user_data.get('email', '')
        self.password_hash = user_data.get('password_hash', '')
        self.name = user_data.get('name', '')
        self.created_at = user_data.get('created_at', datetime.now(UTC))
        self._is_active = user_data.get('is_active', True)
        self.invited_by_user_id = user_data.get('invited_by_user_id')
    
    @property
    def id(self):
        """Return string ID for Flask-Login"""
        return str(self._id) if self._id else None
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        return mongo.db[User.collection_name]
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        if not email:
            return None
        collection = cls.get_collection()
        user_data = collection.find_one({'email': email.lower()})
        return cls(user_data) if user_data else None

    @classmethod
    def count_all(cls):
        return cls.get_collection().count_documents({})
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        if not user_id:
            return None
        collection = cls.get_collection()
        try:
            user_data = collection.find_one({'_id': ObjectId(user_id)})
            return cls(user_data) if user_data else None
        except:
            return None
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        """Save user to MongoDB"""
        collection = self.get_collection()
        data = {
            'email': self.email.lower() if self.email else '',
            'password_hash': self.password_hash,
            'name': self.name,
            'created_at': self.created_at if isinstance(self.created_at, datetime) else datetime.now(UTC),
            'is_active': self.is_active,
            'invited_by_user_id': self.invited_by_user_id,
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self
    
    def has_amazon_connection(self):
        """Check if user has any connected Amazon account."""
        collection = AmazonConnection.get_collection()
        return collection.count_documents({
            'user_id': self.id,
            'is_active': True
        }) > 0

    def get_amazon_connections(self):
        """Return all active Amazon connections for the user."""
        collection = AmazonConnection.get_collection()
        return [
            AmazonConnection(data)
            for data in collection.find({
                'user_id': self.id,
                'is_active': True
            }).sort('marketplace_name', 1)
        ]

    def get_active_connection(self, marketplace_id=None):
        """Get the selected connection, or one for a specific marketplace."""
        collection = AmazonConnection.get_collection()
        query = {
            'user_id': self.id,
            'is_active': True
        }
        if marketplace_id:
            query['marketplace_id'] = marketplace_id
            conn_data = collection.find_one(query)
            return AmazonConnection(conn_data) if conn_data else None

        conn_data = collection.find_one({**query, 'is_selected': True})
        if not conn_data:
            conn_data = collection.find_one(query)
        return AmazonConnection(conn_data) if conn_data else None
    
    # Flask-Login required properties
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return bool(self._is_active)
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        """Return string ID for Flask-Login"""
        return str(self.id) if self.id else None


class AmazonConnection:
    """Amazon Seller Account Connection for MongoDB"""
    
    collection_name = 'amazon_connections'
    
    def __init__(self, data):
        if data is None:
            data = {}
        self._id = data.get('_id')
        self.user_id = data.get('user_id')
        self.seller_id = data.get('seller_id', '')
        self.marketplace_id = data.get('marketplace_id', 'A21TJRUUN4KGV')
        self.marketplace_name = data.get('marketplace_name', 'Amazon.in')
        self.refresh_token_encrypted = data.get('refresh_token_encrypted', '')
        self.access_token_encrypted = data.get('access_token_encrypted')
        self.token_expires_at = data.get('token_expires_at')
        self.is_active = data.get('is_active', True)
        self.is_selected = data.get('is_selected', False)
        self.created_at = data.get('created_at', datetime.now(UTC))
        self.updated_at = data.get('updated_at', datetime.now(UTC))
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        return mongo.db[AmazonConnection.collection_name]
    
    def save(self):
        """Save connection to MongoDB"""
        collection = self.get_collection()
        data = {
            'user_id': self.user_id,
            'seller_id': self.seller_id,
            'marketplace_id': self.marketplace_id,
            'marketplace_name': self.marketplace_name,
            'refresh_token_encrypted': self.refresh_token_encrypted,
            'access_token_encrypted': self.access_token_encrypted,
            'token_expires_at': self.token_expires_at,
            'is_active': self.is_active,
            'is_selected': self.is_selected,
            'created_at': self.created_at if isinstance(self.created_at, datetime) else datetime.now(UTC),
            'updated_at': datetime.now(UTC)
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self


class UpdateLog:
    """Update Log model for MongoDB"""
    
    collection_name = 'update_logs'
    
    @staticmethod
    def get_collection():
        return mongo.db[UpdateLog.collection_name]
    
    @classmethod
    def create(cls, user_id, asin, sku, operation, request_payload, status='PENDING'):
        """Create new update log"""
        collection = cls.get_collection()
        data = {
            'user_id': user_id,
            'asin': asin or '',
            'sku': sku or '',
            'operation': operation,
            'request_payload': request_payload,
            'status': status,
            'error_message': None,
            'amazon_feed_id': None,
            'created_at': datetime.now(UTC),
            'completed_at': None
        }
        return collection.insert_one(data)
    
    @classmethod
    def get_recent_by_user(cls, user_id, limit=10):
        """Get recent logs for user"""
        collection = cls.get_collection()
        return list(collection.find(
            {'user_id': user_id}
        ).sort('created_at', -1).limit(limit))


class BulkUpdateJob:
    """Bulk update job model for MongoDB"""
    
    collection_name = 'bulk_update_jobs'
    
    @staticmethod
    def get_collection():
        return mongo.db[BulkUpdateJob.collection_name]
    
    @classmethod
    def create(cls, user_id, job_name, total_records):
        """Create new bulk job"""
        collection = cls.get_collection()
        data = {
            'user_id': user_id,
            'job_name': job_name,
            'total_records': total_records,
            'processed_records': 0,
            'success_count': 0,
            'failed_count': 0,
            'status': 'PENDING',
            'errors': [],
            'created_at': datetime.now(UTC),
            'started_at': None,
            'completed_at': None
        }
        result = collection.insert_one(data)
        return result.inserted_id


class Invitation:
    """Invite-only registration records."""

    collection_name = 'invitations'

    def __init__(self, data=None):
        data = data or {}
        self._id = data.get('_id')
        self.email = (data.get('email') or '').lower()
        self.token = data.get('token') or secrets.token_urlsafe(24)
        self.invited_by_user_id = data.get('invited_by_user_id')
        self.status = data.get('status', 'PENDING')
        self.created_at = data.get('created_at', datetime.now(UTC))
        self.expires_at = data.get('expires_at', datetime.now(UTC) + timedelta(days=7))
        self.accepted_at = data.get('accepted_at')
        self.accepted_user_id = data.get('accepted_user_id')

    @staticmethod
    def get_collection():
        return mongo.db[Invitation.collection_name]

    def save(self):
        collection = self.get_collection()
        data = {
            'email': self.email,
            'token': self.token,
            'invited_by_user_id': self.invited_by_user_id,
            'status': self.status,
            'created_at': self.created_at if isinstance(self.created_at, datetime) else datetime.now(UTC),
            'expires_at': self.expires_at if isinstance(self.expires_at, datetime) else datetime.now(UTC) + timedelta(days=7),
            'accepted_at': self.accepted_at,
            'accepted_user_id': self.accepted_user_id,
        }

        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self

    @classmethod
    def find_by_user(cls, user_id, marketplace_id=None, active_only=True):
        """Find one connection for a user, optionally filtered by marketplace."""
        query = {'user_id': user_id}
        if active_only:
            query['is_active'] = True
        if marketplace_id:
            query['marketplace_id'] = marketplace_id
        data = cls.get_collection().find_one(query)
        return cls(data) if data else None

    @classmethod
    def deactivate_selected_for_user(cls, user_id):
        """Clear active selection marker for all of the user's live connections."""
        cls.get_collection().update_many(
            {'user_id': user_id, 'is_active': True, 'is_selected': True},
            {'$set': {'is_selected': False, 'updated_at': datetime.now(UTC)}}
        )

    @classmethod
    def upsert_for_marketplace(cls, user_id, marketplace_id, defaults):
        """Create or update a marketplace connection for a user."""
        collection = cls.get_collection()
        existing = collection.find_one({
            'user_id': user_id,
            'marketplace_id': marketplace_id
        })

        payload = {
            **defaults,
            'user_id': user_id,
            'marketplace_id': marketplace_id,
            'updated_at': datetime.now(UTC),
        }

        if existing:
            collection.update_one({'_id': existing['_id']}, {'$set': payload})
            payload['_id'] = existing['_id']
            if 'created_at' not in payload:
                payload['created_at'] = existing.get('created_at', datetime.now(UTC))
            return cls(payload)

        payload.setdefault('created_at', datetime.now(UTC))
        result = collection.insert_one(payload)
        payload['_id'] = result.inserted_id
        return cls(payload)

    @classmethod
    def deactivate_selected_for_user(cls, user_id):
        cls.get_collection().update_many(
            {'user_id': user_id, 'is_selected': True},
            {'$set': {'is_selected': False, 'updated_at': datetime.now(UTC)}}
        )

    @classmethod
    def upsert_for_marketplace(cls, user_id, marketplace_id, defaults):
        collection = cls.get_collection()
        existing = collection.find_one({
            'user_id': user_id,
            'marketplace_id': marketplace_id,
        })
        if existing:
            collection.update_one(
                {'_id': existing['_id']},
                {'$set': {**defaults, 'updated_at': datetime.now(UTC)}}
            )
            existing.update(defaults)
            existing['updated_at'] = datetime.now(UTC)
            return cls(existing)

        connection = cls({
            'user_id': user_id,
            'marketplace_id': marketplace_id,
            **defaults,
        })
        connection.save()
        return connection

    @classmethod
    def find_valid_by_token(cls, token):
        if not token:
            return None
        now = datetime.now(UTC)
        data = cls.get_collection().find_one({
            'token': token,
            'status': 'PENDING',
            'expires_at': {'$gt': now},
        })
        return cls(data) if data else None

    @classmethod
    def find_latest_pending_for_email(cls, email):
        if not email:
            return None
        data = cls.get_collection().find_one({
            'email': email.lower(),
            'status': 'PENDING',
        })
        return cls(data) if data else None

    @classmethod
    def get_recent_for_inviter(cls, inviter_user_id, limit=20):
        return list(
            cls.get_collection().find({'invited_by_user_id': inviter_user_id}).sort('created_at', -1).limit(limit)
        )

    def mark_accepted(self, user_id):
        self.status = 'ACCEPTED'
        self.accepted_user_id = user_id
        self.accepted_at = datetime.now(UTC)
        self.save()

