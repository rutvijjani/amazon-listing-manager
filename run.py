#!/usr/bin/env python3
"""
Amazon Listing Manager - Entry Point (MongoDB Version)
Run with: python run.py
"""

from app import create_app, mongo
from app.models import User, AmazonConnection, UpdateLog, BulkUpdateJob

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'mongo': mongo,
        'User': User,
        'AmazonConnection': AmazonConnection,
        'UpdateLog': UpdateLog,
        'BulkUpdateJob': BulkUpdateJob
    }

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
