"""
Database Models for Amazon Listing Manager
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from app import db


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    amazon_connections = db.relationship('AmazonConnection', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    update_logs = db.relationship('UpdateLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    bulk_update_jobs = db.relationship('BulkUpdateJob', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_active_connection(self):
        """Get user's active Amazon connection"""
        return self.amazon_connections.filter_by(is_active=True).first()
    
    def has_amazon_connection(self):
        """Check if user has connected Amazon account"""
        return self.amazon_connections.filter_by(is_active=True).count() > 0
    
    def __repr__(self):
        return f'<User {self.email}>'


class AmazonConnection(db.Model):
    """Amazon Seller Account Connection"""
    __tablename__ = 'amazon_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Amazon Seller Info
    seller_id = db.Column(db.String(50), nullable=False)
    marketplace_id = db.Column(db.String(20), nullable=False, default='A21TJRUUN4KGV')  # India default
    marketplace_name = db.Column(db.String(50), default='Amazon.in')
    
    # OAuth Tokens (encrypted)
    refresh_token_encrypted = db.Column(db.Text, nullable=False)
    access_token_encrypted = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AmazonConnection {self.seller_id} ({self.marketplace_name})>'


class UpdateLog(db.Model):
    """Log of all listing updates"""
    __tablename__ = 'update_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Listing Info
    asin = db.Column(db.String(20), nullable=False, index=True)
    sku = db.Column(db.String(50), index=True)
    
    # Operation Details
    operation = db.Column(db.String(50), nullable=False)  # UPDATE_PRICE, UPDATE_CONTENT, etc.
    request_payload = db.Column(db.Text)  # JSON
    response_payload = db.Column(db.Text)  # JSON
    
    # Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, SUCCESS, FAILED
    error_message = db.Column(db.Text)
    
    # Amazon Response
    amazon_feed_id = db.Column(db.String(100))
    amazon_submission_id = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def set_request_payload(self, data):
        """Store request as JSON"""
        self.request_payload = json.dumps(data, indent=2)
    
    def get_request_payload(self):
        """Get request as dict"""
        return json.loads(self.request_payload) if self.request_payload else {}
    
    def set_response_payload(self, data):
        """Store response as JSON"""
        self.response_payload = json.dumps(data, indent=2)
    
    def get_response_payload(self):
        """Get response as dict"""
        return json.loads(self.response_payload) if self.response_payload else {}
    
    def mark_success(self):
        """Mark log as successful"""
        self.status = 'SUCCESS'
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error):
        """Mark log as failed"""
        self.status = 'FAILED'
        self.error_message = str(error)
        self.completed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<UpdateLog {self.asin} - {self.operation} - {self.status}>'


class BulkUpdateJob(db.Model):
    """Bulk update job tracking"""
    __tablename__ = 'bulk_update_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Job Info
    job_name = db.Column(db.String(200))
    filename = db.Column(db.String(255))
    total_records = db.Column(db.Integer, default=0)
    processed_records = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PROCESSING, COMPLETED, FAILED
    
    # Error details
    errors = db.Column(db.Text)  # JSON array of errors
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    def set_errors(self, error_list):
        """Store errors as JSON"""
        self.errors = json.dumps(error_list, indent=2)
    
    def get_errors(self):
        """Get errors as list"""
        return json.loads(self.errors) if self.errors else []
    
    def __repr__(self):
        return f'<BulkUpdateJob {self.job_name} - {self.status}>'
