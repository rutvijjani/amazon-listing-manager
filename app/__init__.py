"""
Amazon Listing Manager - Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Amazon SP-API Config
    app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
    app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    app.config['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
    app.config['LWA_CLIENT_ID'] = os.getenv('LWA_CLIENT_ID')
    app.config['LWA_CLIENT_SECRET'] = os.getenv('LWA_CLIENT_SECRET')
    app.config['SP_API_ROLE_ARN'] = os.getenv('SP_API_ROLE_ARN')
    app.config['AMAZON_REDIRECT_URI'] = os.getenv('AMAZON_REDIRECT_URI', 'http://localhost:5000/auth/amazon/callback')
    app.config['TOKEN_ENCRYPTION_KEY'] = os.getenv('TOKEN_ENCRYPTION_KEY')
    
    # Sandbox Direct Credentials (optional - for testing without OAuth)
    app.config['SANDBOX_REFRESH_TOKEN'] = os.getenv('SANDBOX_REFRESH_TOKEN')
    app.config['SANDBOX_SELLER_ID'] = os.getenv('SANDBOX_SELLER_ID')
    app.config['SANDBOX_MARKETPLACE_ID'] = os.getenv('SANDBOX_MARKETPLACE_ID', 'A21TJRUUN4KGV')
    
    # Initialize extensions
    db.init_app(app)
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
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
