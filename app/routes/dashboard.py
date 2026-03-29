"""
Dashboard Routes
"""

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app.services.listing_service import ListingService
from app.models import UpdateLog, BulkUpdateJob

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard"""
    # Check if user has Amazon connection
    has_connection = current_user.has_amazon_connection()
    connection = current_user.get_active_connection()
    
    # Get recent activity
    recent_logs = UpdateLog.query.filter_by(user_id=current_user.id)\
        .order_by(UpdateLog.created_at.desc())\
        .limit(10).all()
    
    # Get stats
    stats = {
        'total_updates': UpdateLog.query.filter_by(user_id=current_user.id).count(),
        'successful_updates': UpdateLog.query.filter_by(user_id=current_user.id, status='SUCCESS').count(),
        'failed_updates': UpdateLog.query.filter_by(user_id=current_user.id, status='FAILED').count(),
        'pending_updates': UpdateLog.query.filter_by(user_id=current_user.id, status='PENDING').count(),
    }
    
    # Get recent bulk jobs
    recent_jobs = BulkUpdateJob.query.filter_by(user_id=current_user.id)\
        .order_by(BulkUpdateJob.created_at.desc())\
        .limit(5).all()
    
    return render_template('dashboard.html',
                         has_connection=has_connection,
                         connection=connection,
                         recent_logs=recent_logs,
                         stats=stats,
                         recent_jobs=recent_jobs)


@bp.route('/settings')
@login_required
def settings():
    """General settings page"""
    return render_template('settings/general.html', user=current_user)


@bp.route('/settings/amazon')
@login_required
def amazon_settings():
    """Amazon connection settings"""
    connection = current_user.get_active_connection()
    
    from app.services.auth_service import AmazonOAuth
    marketplaces = AmazonOAuth.MARKETPLACES
    
    return render_template('settings/amazon_connect.html',
                         connection=connection,
                         marketplaces=marketplaces)
