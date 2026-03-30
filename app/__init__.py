"""
Amazon Listing Manager - Flask Application Factory (MongoDB Version)
"""

from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os
import certifi

# Initialize extensions
mongo = PyMongo()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name=None):
    """Application factory pattern for MongoDB"""
    
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    config_keys = [
        'TOKEN_ENCRYPTION_KEY',
        'LWA_CLIENT_ID',
        'LWA_CLIENT_SECRET',
        'AMAZON_REDIRECT_URI',
        'AMAZON_LOGIN_URI',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'SP_API_ROLE_ARN',
        'SPAPI_APPLICATION_ID',
        'SPAPI_AUTH_VERSION',
        'SANDBOX_REFRESH_TOKEN',
        'SANDBOX_SELLER_ID',
        'SANDBOX_MARKETPLACE_ID',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'MAIL_FROM',
    ]
    for key in config_keys:
        value = os.getenv(key)
        if value:
            app.config[key] = value
    
    # MongoDB Configuration - Simplified with certifi for SSL
    mongo_uri = os.getenv('MONGODB_URI')
    if mongo_uri:
        # Use certifi for proper SSL certificates
        app.config['MONGO_URI'] = mongo_uri
        app.config['MONGO_CONNECT'] = False
        print("MongoDB Atlas configured")
    else:
        app.config['MONGO_URI'] = 'mongodb://localhost:27017/amazon_listing_manager'
        print("Using local MongoDB")
    
    # Initialize extensions with SSL certificate
    try:
        mongo.init_app(app, uri=app.config['MONGO_URI'], 
                       connect=False,
                       tlsCAFile=certifi.where())
        print("MongoDB initialized")
    except Exception as e:
        print(f"MongoDB init error: {e}")
    
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.listings import bp as listings_bp
    from app.routes.api import bp as api_bp
    from app.routes.sandbox import bp as sandbox_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(listings_bp, url_prefix='/listings')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(sandbox_bp)

    @app.get('/health')
    def health():
        return {'status': 'ok'}, 200
    
    # Create indexes for MongoDB
    with app.app_context():
        try:
            mongo.db.users.create_index('email', unique=True)
            mongo.db.amazon_connections.create_index('user_id')
            mongo.db.update_logs.create_index('user_id')
            mongo.db.bulk_update_jobs.create_index('user_id')
            mongo.db.invitations.create_index('email')
            mongo.db.invitations.create_index('token', unique=True)
            mongo.db.invitations.create_index('invited_by_user_id')
            print("MongoDB indexes created")
        except Exception as e:
            print(f"Index creation warning: {e}")
    
    # Load user for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.find_by_id(user_id)
    
    return app

