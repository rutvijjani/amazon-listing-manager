#!/usr/bin/env python3
"""
Amazon Listing Manager - Entry Point
Run with: python run.py
"""

from app import create_app, db
from app.models import User, AmazonConnection, UpdateLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'AmazonConnection': AmazonConnection,
        'UpdateLog': UpdateLog
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
