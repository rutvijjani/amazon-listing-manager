"""
Dashboard Routes for MongoDB
"""

from datetime import datetime, UTC

from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required, current_user
from app.models import BulkUpdateJob, Invitation, UpdateLog

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard for MongoDB"""
    # Check if user has Amazon connection
    has_connection = current_user.has_amazon_connection()
    connection = current_user.get_active_connection()
    
    # Get recent activity (always scoped to the current user)
    recent_logs = UpdateLog.get_recent_by_user(current_user.id, limit=10)
    recent_invites = Invitation.get_recent_for_inviter(current_user.id, limit=5)
    
    # Get stats
    collection = UpdateLog.get_collection()
    stats = {
        'total_updates': collection.count_documents({'user_id': current_user.id}),
        'successful_updates': collection.count_documents({'user_id': current_user.id, 'status': 'SUCCESS'}),
        'failed_updates': collection.count_documents({'user_id': current_user.id, 'status': 'FAILED'}),
        'pending_updates': collection.count_documents({'user_id': current_user.id, 'status': 'PENDING'}),
        'pending_invites': Invitation.get_collection().count_documents({'invited_by_user_id': current_user.id, 'status': 'PENDING'}),
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
                         recent_invites=recent_invites,
                         stats=stats,
                         recent_jobs=recent_jobs)


@bp.route('/settings')
@login_required
def settings():
    """General settings page"""
    return redirect(url_for('dashboard.amazon_settings'))


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


@bp.route('/team-access')
@login_required
def team_access():
    """Invite-only access management page."""
    invites = Invitation.get_recent_for_inviter(current_user.id, limit=50)
    now = datetime.now(UTC)
    return render_template('team_access.html', invites=invites, now=now)
