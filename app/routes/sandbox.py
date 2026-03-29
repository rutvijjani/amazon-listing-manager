"""
Sandbox Auto-Connect Routes
For direct sandbox credentials without OAuth flow
"""

from flask import Blueprint, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import AmazonConnection
from app.services.auth_service import TokenEncryption

bp = Blueprint('sandbox', __name__, url_prefix='/sandbox')


@bp.route('/connect')
@login_required
def auto_connect():
    """
    Auto-connect using sandbox credentials from environment
    No OAuth flow needed!
    """
    
    # Get sandbox credentials from environment
    refresh_token = current_app.config.get('SANDBOX_REFRESH_TOKEN')
    seller_id = current_app.config.get('SANDBOX_SELLER_ID')
    marketplace_id = current_app.config.get('SANDBOX_MARKETPLACE_ID', 'A21TJRUUN4KGV')
    
    if not refresh_token:
        flash('Sandbox credentials not configured. Please add SANDBOX_REFRESH_TOKEN to .env file', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    if not seller_id:
        flash('Sandbox Seller ID not configured. Please add SANDBOX_SELLER_ID to .env file', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    try:
        encryption = TokenEncryption()
        
        # Deactivate existing connections
        AmazonConnection.query.filter_by(user_id=current_user.id, is_active=True).update({
            'is_active': False
        })
        
        # Create new sandbox connection
        connection = AmazonConnection(
            user_id=current_user.id,
            seller_id=seller_id,
            marketplace_id=marketplace_id,
            marketplace_name='Amazon.in (Sandbox)',
            refresh_token_encrypted=encryption.encrypt(refresh_token),
            access_token_encrypted=None,
            is_active=True
        )
        
        db.session.add(connection)
        db.session.commit()
        
        flash(f'Successfully connected to Amazon Sandbox! Seller ID: {seller_id}', 'success')
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to connect sandbox: {str(e)}', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/disconnect')
@login_required
def disconnect():
    """Disconnect sandbox connection"""
    connection = current_user.get_active_connection()
    
    if connection:
        connection.is_active = False
        db.session.commit()
        flash('Sandbox connection disconnected.', 'info')
    else:
        flash('No sandbox connection found.', 'warning')
    
    return redirect(url_for('dashboard.index'))
