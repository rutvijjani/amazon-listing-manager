"""
WSGI entry point for PythonAnywhere deployment
"""

import sys
import os

# Add project path
path = '/home/yourusername/my-flask-app'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import Flask app
from run import app as application
