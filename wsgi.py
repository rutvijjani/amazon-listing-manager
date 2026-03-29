"""
WSGI entry point for PythonAnywhere deployment
"""

import os
import sys

# Add project path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import Flask app
from run import app as application
