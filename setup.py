#!/usr/bin/env python3
"""
Setup script for Amazon Listing Manager
Helps configure the application for first use
"""

import os
import sys
import secrets

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate token encryption key"""
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    except ImportError:
        return None

def setup_env_file():
    """Create or update .env file"""
    env_file = '.env'
    
    print("=" * 60)
    print("Amazon Listing Manager - Setup Wizard")
    print("=" * 60)
    print()
    
    # Check if .env exists
    if os.path.exists(env_file):
        print(f"'{env_file}' already exists.")
        response = input("Do you want to update it? (yes/no): ").lower()
        if response not in ['yes', 'y']:
            print("Setup cancelled.")
            return
    
    print("\nPlease enter your Amazon SP-API credentials:")
    print("(Press Enter to skip if you don't have them yet)")
    print()
    
    # AWS Credentials
    aws_access_key = input("AWS Access Key ID: ").strip()
    aws_secret_key = input("AWS Secret Access Key: ").strip()
    aws_region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
    
    # LWA Credentials
    print("\n--- Login with Amazon Credentials ---")
    lwa_client_id = input("LWA Client ID: ").strip()
    lwa_client_secret = input("LWA Client Secret: ").strip()
    
    # SP-API Role
    print("\n--- SP-API Configuration ---")
    sp_api_role = input("SP-API Role ARN: ").strip()
    
    # Sandbox Credentials
    print("\n--- Sandbox Credentials (Optional - for testing) ---")
    sandbox_token = input("Sandbox Refresh Token: ").strip()
    sandbox_seller = input("Sandbox Seller ID: ").strip()
    
    # Generate keys
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()
    
    # Create .env content
    env_content = f"""# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY={secret_key}

# Database
MONGODB_URI=mongodb://localhost:27017/amazon_listing_manager

# Token Encryption
TOKEN_ENCRYPTION_KEY={encryption_key or 'generate-using-python-cryptography'}

# AWS Credentials
AWS_ACCESS_KEY_ID={aws_access_key or 'your-access-key'}
AWS_SECRET_ACCESS_KEY={aws_secret_key or 'your-secret-key'}
AWS_REGION={aws_region}

# Login with Amazon
LWA_CLIENT_ID={lwa_client_id or 'your-client-id'}
LWA_CLIENT_SECRET={lwa_client_secret or 'your-client-secret'}
AMAZON_LOGIN_URI=http://localhost:5000/auth/amazon/connect

# SP-API
SP_API_ROLE_ARN={sp_api_role or 'your-role-arn'}
AMAZON_REDIRECT_URI=http://localhost:5000/auth/amazon/callback
SPAPI_APPLICATION_ID=your-application-id
SPAPI_AUTH_VERSION=beta

# Sandbox (Optional)
SANDBOX_REFRESH_TOKEN={sandbox_token or ''}
SANDBOX_SELLER_ID={sandbox_seller or ''}
SANDBOX_MARKETPLACE_ID=A21TJRUUN4KGV
"""
    
    # Write to file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print()
    print("=" * 60)
    print(f"✅ {env_file} created successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review .env file and update any missing values")
    print("2. Run: python run.py")
    print("3. Open browser: http://localhost:5000")
    print()

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    
    required = {
        'flask': 'flask',
        'flask_pymongo': 'flask_pymongo',
        'pymongo': 'pymongo',
        'flask_login': 'flask_login',
        'requests': 'requests',
        'boto3': 'boto3',
        'cryptography': 'cryptography',
    }
    missing = []
    
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages. Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("\n✅ All dependencies installed!")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            check_dependencies()
        elif sys.argv[1] == '--generate-keys':
            print("Secret Key:", generate_secret_key())
            print("Encryption Key:", generate_encryption_key())
    else:
        if check_dependencies():
            setup_env_file()
