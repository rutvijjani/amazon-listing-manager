"""
MongoDB Models for Amazon Listing Manager
"""

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
from flask_login import UserMixin


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
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.is_active = user_data.get('is_active', True)
    
    @property
    def id(self):
        """Return string ID for Flask-Login"""
        return str(self._id) if self._id else None
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        return current_app.mongo.db[User.collection_name]
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        if not email:
            return None
        collection = cls.get_collection()
        user_data = collection.find_one({'email': email.lower()})
        return cls(user_data) if user_data else None
    
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
            'created_at': self.created_at if isinstance(self.created_at, datetime) else datetime.utcnow(),
            'is_active': self.is_active
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self
    
    def has_amazon_connection(self):
        """Check if user has connected Amazon account"""
        collection = AmazonConnection.get_collection()
        return collection.count_documents({
            'user_id': self.id,
            'is_active': True
        }) > 0
    
    def get_active_connection(self):
        """Get user's active Amazon connection"""
        collection = AmazonConnection.get_collection()
        conn_data = collection.find_one({
            'user_id': self.id,
            'is_active': True
        })
        return AmazonConnection(conn_data) if conn_data else None
    
    # Flask-Login required properties
    @property
    def is_authenticated(self):
        return True
    
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
        self.created_at = data.get('created_at', datetime.utcnow())
        self.updated_at = data.get('updated_at', datetime.utcnow())
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        return current_app.mongo.db[AmazonConnection.collection_name]
    
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
            'created_at': self.created_at if isinstance(self.created_at, datetime) else datetime.utcnow(),
            'updated_at': datetime.utcnow()
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
        return current_app.mongo.db[UpdateLog.collection_name]
    
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
            'created_at': datetime.utcnow(),
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
        return current_app.mongo.db[BulkUpdateJob.collection_name]
    
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
            'created_at': datetime.utcnow(),
            'started_at': None,
            'completed_at': None
        }
        result = collection.insert_one(data)
        return result.inserted_id
