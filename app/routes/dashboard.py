"""
Dashboard Routes for MongoDB
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import User, UpdateLog, BulkUpdateJob

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard for MongoDB"""
    # Check if user has Amazon connection
    has_connection = current_user.has_amazon_connection()
    connection = current_user.get_active_connection()
    
    # Get recent activity
    recent_logs = UpdateLog.get_recent_by_user(current_user.id, limit=10)
    
    # Get stats
    collection = UpdateLog.get_collection()
    stats = {
        'total_updates': collection.count_documents({'user_id': current_user.id}),
        'successful_updates': collection.count_documents({'user_id': current_user.id, 'status': 'SUCCESS'}),
        'failed_updates': collection.count_documents({'user_id': current_user.id, 'status': 'FAILED'}),
        'pending_updates': collection.count_documents({'user_id': current_user.id, 'status': 'PENDING'}),
    }
    
    # Get recent bulk jobs
    jobs_collection = BulkUpdateJob.get_collection()
    recent_jobs = list(jobs_collection.find(
        {'user_id': current_user.id}
    ).sort('created_at', -1).limit(5))
    
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
