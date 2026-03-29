"""
Authentication Routes for MongoDB
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from datetime import datetime

from app import mongo
from app.models import User, AmazonConnection
from app.services.auth_service import AmazonOAuth, TokenEncryption

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration for MongoDB"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        name = request.form.get('name', '').strip()
        
        # Validation
        errors = []
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check if email exists
        existing_user = User.find_by_email(email)
        if existing_user:
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', email=email, name=name)
        
        # Create user
        try:
            user = User({'email': email, 'name': name})
            user.set_password(password)
            user.save()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('auth/register.html', email=email, name=name)
    
    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login for MongoDB"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        user = User.find_by_email(email)
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return render_template('auth/login.html', email=email)
            
            login_user(user, remember=remember)
            
            # Get next page
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            
            flash(f'Welcome back, {user.name or user.email}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html', email=email)
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ==================== Amazon OAuth Routes ====================

@bp.route('/amazon/connect')
@login_required
def amazon_connect():
    """Redirect to Amazon OAuth authorization"""
    oauth = AmazonOAuth()
    
    # Store state in session for verification
    import secrets
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Get marketplace from query param or default to India
    marketplace_id = request.args.get('marketplace', 'A21TJRUUN4KGV')
    
    auth_url = oauth.get_authorization_url(state=state, marketplace_id=marketplace_id)
    return redirect(auth_url)


@bp.route('/amazon/callback')
@login_required
def amazon_callback():
    """Handle Amazon OAuth callback"""
    # Verify state
    state = request.args.get('state')
    stored_state = session.get('oauth_state')
    
    if not state or state != stored_state:
        flash('Invalid OAuth state. Please try again.', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    # Check for error
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        flash(f'Amazon authorization failed: {error_description}', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        flash('Authorization code not received.', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    try:
        # Exchange code for tokens
        oauth = AmazonOAuth()
        token_data = oauth.exchange_code_for_tokens(code)
        
        encryption = TokenEncryption()
        
        # Deactivate existing connections
        collection = AmazonConnection.get_collection()
        collection.update_many(
            {'user_id': current_user.id, 'is_active': True},
            {'$set': {'is_active': False}}
        )
        
        # Create new connection
        connection = AmazonConnection({
            'user_id': current_user.id,
            'seller_id': 'pending',
            'marketplace_id': 'A21TJRUUN4KGV',
            'marketplace_name': 'Amazon.in',
            'refresh_token_encrypted': encryption.encrypt(token_data['refresh_token']),
            'access_token_encrypted': encryption.encrypt(token_data.get('access_token')),
            'is_active': True
        })
        connection.save()
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        
        flash('Amazon account connected successfully!', 'success')
        return redirect(url_for('dashboard.amazon_settings'))
        
    except Exception as e:
        flash(f'Failed to connect Amazon account: {str(e)}', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/amazon/disconnect', methods=['POST'])
@login_required
def amazon_disconnect():
    """Disconnect Amazon account"""
    collection = AmazonConnection.get_collection()
    result = collection.update_many(
        {'user_id': current_user.id, 'is_active': True},
        {'$set': {'is_active': False}}
    )
    
    if result.modified_count > 0:
        flash('Amazon account disconnected.', 'info')
    else:
        flash('No Amazon account connected.', 'warning')
    
    return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/amazon/update-seller-id', methods=['POST'])
@login_required
def update_seller_id():
    """Update seller ID for connected account"""
    seller_id = request.form.get('seller_id', '').strip()
    
    if not seller_id:
        flash('Seller ID is required', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    collection = AmazonConnection.get_collection()
    result = collection.find_one_and_update(
        {'user_id': current_user.id, 'is_active': True},
        {'$set': {'seller_id': seller_id, 'updated_at': datetime.utcnow()}}
    )
    
    if result:
        flash('Seller ID updated successfully', 'success')
    else:
        flash('No active Amazon connection found', 'danger')
    
    return redirect(url_for('dashboard.amazon_settings'))
