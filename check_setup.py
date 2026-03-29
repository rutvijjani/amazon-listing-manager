#!/usr/bin/env python3
"""
Setup Verification Script for Amazon Listing Manager
Checks if all required configurations are present
"""

import os
import sys
from dotenv import load_dotenv

def check_setup():
    """Verify all required configurations"""
    load_dotenv()
    
    print("=" * 60)
    print("Amazon Listing Manager - Setup Verification")
    print("=" * 60)
    
    required_vars = {
        'SECRET_KEY': 'Flask secret key',
        'AWS_ACCESS_KEY_ID': 'AWS IAM Access Key',
        'AWS_SECRET_ACCESS_KEY': 'AWS IAM Secret Key',
        'AWS_REGION': 'AWS Region',
        'LWA_CLIENT_ID': 'Login with Amazon Client ID',
        'LWA_CLIENT_SECRET': 'Login with Amazon Client Secret',
        'SP_API_ROLE_ARN': 'SP-API IAM Role ARN',
        'AMAZON_REDIRECT_URI': 'OAuth Redirect URI',
        'TOKEN_ENCRYPTION_KEY': 'Token Encryption Key'
    }
    
    missing = []
    present = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value not in ['AKIA...', 'amzn1.application-oa2-client....', 'your-', 'arn:aws:iam::...', 'http://localhost:5000/auth/amazon/callback']:
            present.append((var, description))
        else:
            missing.append((var, description))
    
    print("\n✅ Configured Variables:")
    print("-" * 40)
    for var, desc in present:
        # Mask sensitive values
        value = os.getenv(var)
        if 'KEY' in var or 'SECRET' in var:
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
        print(f"  ✓ {var}")
        print(f"    {desc}: {display_value}")
    
    if missing:
        print("\n❌ Missing/Invalid Variables:")
        print("-" * 40)
        for var, desc in missing:
            print(f"  ✗ {var}")
            print(f"    {desc}: NOT SET")
        print("\n⚠️  Please configure these in your .env file")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All configurations are set!")
    print("=" * 60)
    print("\nYou can now run the app with: python run.py")
    print("Then open: http://localhost:5000")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Dependencies...")
    print("-" * 40)
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'requests',
        'boto3',
        'cryptography',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('_', ''))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def generate_encryption_key():
    """Generate a new encryption key"""
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        print("\n🔐 Generated Token Encryption Key:")
        print("-" * 40)
        print(key.decode())
        print("-" * 40)
        print("Copy this to your .env file as TOKEN_ENCRYPTION_KEY")
    except ImportError:
        print("\n⚠️  Install cryptography package first:")
        print("   pip install cryptography")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-key':
        generate_encryption_key()
    else:
        deps_ok = check_dependencies()
        config_ok = check_setup()
        
        if not config_ok:
            print("\n🔧 Need to generate encryption key? Run:")
            print("   python check_setup.py --generate-key")
        
        print("\n" + "=" * 60)
        if deps_ok and config_ok:
            print("🚀 Ready to launch! Run: python run.py")
        else:
            print("⚠️  Please fix the issues above before running the app")
        print("=" * 60)
