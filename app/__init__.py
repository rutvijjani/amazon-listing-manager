"""
Amazon Listing Manager - Flask Application Factory (MongoDB Version)
"""

from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from pymongo import MongoClient
import os

# Initialize extensions
mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory pattern for MongoDB"""
    
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # MongoDB Configuration - Using direct client for better SSL handling
    mongo_uri = os.getenv('MONGODB_URI')
    if mongo_uri:
        try:
            # Create client with SSL settings
            client = MongoClient(
                mongo_uri,
                ssl=True,
                ssl_cert_reqs=False,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000
            )
            # Test connection
            client.admin.command('ping')
            app.config['MONGO_URI'] = mongo_uri
            app.mongo_client = client
            app.db = client.get_default_database()
            print(f"✅ MongoDB Atlas Connected")
        except Exception as e:
            print(f"⚠️ MongoDB Connection Error: {e}")
            # Fallback
            app.config['MONGO_URI'] = mongo_uri
    else:
        app.config['MONGO_URI'] = 'mongodb://localhost:27017/amazon_listing_manager'
        print(f"⚠️ Using local MongoDB")
    
    # Initialize extensions
    mongo.init_app(app)
    login_manager.init_app(app)
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
    
    # Create indexes for MongoDB
    with app.app_context():
        try:
            mongo.db.users.create_index('email', unique=True)
            mongo.db.amazon_connections.create_index('user_id')
            mongo.db.update_logs.create_index('user_id')
            mongo.db.bulk_update_jobs.create_index('user_id')
            print("✅ MongoDB indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
    
    # Load user for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.find_by_id(user_id)
    
    return app
