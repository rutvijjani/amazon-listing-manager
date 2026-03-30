"""
Authentication Routes for MongoDB
"""

import smtplib
from datetime import datetime, timedelta, UTC
from email.message import EmailMessage
from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import login_user, logout_user, login_required, current_user

from app import mongo
from app.models import AmazonConnection, Invitation, User
from app.services.auth_service import AmazonOAuth, TokenEncryption

bp = Blueprint('auth', __name__)


def _register_invite_context():
    """Resolve invite token and invitation shown on the register page."""
    invite_token = (request.values.get('invite') or request.args.get('invite') or '').strip()
    invitation = Invitation.find_valid_by_token(invite_token) if invite_token else None
    return invite_token, invitation


def _send_invite_email(email, invite_url):
    """Send invite email when SMTP configuration is available."""
    smtp_host = current_app.config.get('SMTP_HOST')
    smtp_port = int(current_app.config.get('SMTP_PORT', 587))
    smtp_username = current_app.config.get('SMTP_USERNAME')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    mail_from = current_app.config.get('MAIL_FROM')

    if not all([smtp_host, smtp_username, smtp_password, mail_from]):
        return False

    message = EmailMessage()
    message['Subject'] = 'You have been invited to Amazon Listing Manager'
    message['From'] = mail_from
    message['To'] = email
    message.set_content(
        "You can now create your account for Amazon Listing Manager.\n\n"
        f"Register using this secure invite link:\n{invite_url}\n\n"
        "This link is valid for 7 days and only works for this email address."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)
    return True


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration for MongoDB"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    invite_token, invitation = _register_invite_context()
    bootstrap_allowed = User.count_all() == 0

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        name = request.form.get('name', '').strip()
        invite_token = request.form.get('invite_token', invite_token).strip()
        invitation = Invitation.find_valid_by_token(invite_token) if invite_token else None
        
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

        if not bootstrap_allowed:
            if not invitation:
                errors.append('A valid invitation link is required to register')
            elif invitation.email != email:
                errors.append('This invitation only works for the invited email address')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'auth/register.html',
                email=email,
                name=name,
                invitation=invitation,
                invite_token=invite_token,
                bootstrap_allowed=bootstrap_allowed,
            )
        
        # Create user
        try:
            user = User({
                'email': email,
                'name': name,
                'invited_by_user_id': invitation.invited_by_user_id if invitation else None,
            })
            user.set_password(password)
            user.save()

            if invitation:
                invitation.mark_accepted(user.id)
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template(
                'auth/register.html',
                email=email,
                name=name,
                invitation=invitation,
                invite_token=invite_token,
                bootstrap_allowed=bootstrap_allowed,
            )
    
    return render_template(
        'auth/register.html',
        invitation=invitation,
        invite_token=invite_token,
        bootstrap_allowed=bootstrap_allowed,
    )


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
    """Handle SP-API website authorization workflow."""
    oauth = AmazonOAuth()

    # Step 2 of website authorization flow:
    # Amazon calls our login URI with amazon_callback_uri + amazon_state.
    amazon_callback_uri = request.args.get('amazon_callback_uri')
    amazon_state = request.args.get('amazon_state')
    selling_partner_id = request.args.get('selling_partner_id')
    if amazon_callback_uri and amazon_state:
        import secrets
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        if selling_partner_id:
            session['oauth_selling_partner_id'] = selling_partner_id
        callback_url = oauth.get_callback_redirect_url(
            amazon_callback_uri=amazon_callback_uri,
            amazon_state=amazon_state,
            state=state
        )
        return redirect(callback_url)

    # Step 1 of website authorization flow:
    # user clicks authorize from our app.
    import secrets
    initial_state = secrets.token_urlsafe(32)
    session['oauth_init_state'] = initial_state

    marketplace_id = request.args.get('marketplace', 'A21TJRUUN4KGV')
    session['oauth_marketplace_id'] = marketplace_id
    session['oauth_marketplace_name'] = AmazonOAuth.get_marketplace_name(marketplace_id)

    auth_url = oauth.get_authorization_url(state=initial_state, marketplace_id=marketplace_id)
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
    
    # Get authorization code from SP-API website authorization workflow
    code = request.args.get('spapi_oauth_code') or request.args.get('code')
    if not code:
        flash('Authorization code not received.', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))
    
    try:
        # Exchange code for tokens
        oauth = AmazonOAuth()
        token_data = oauth.exchange_code_for_tokens(code)
        
        encryption = TokenEncryption()
        marketplace_id = session.get('oauth_marketplace_id', 'A21TJRUUN4KGV')
        marketplace_name = session.get('oauth_marketplace_name', AmazonOAuth.get_marketplace_name(marketplace_id))
        expires_in = token_data.get('expires_in')
        selling_partner_id = request.args.get('selling_partner_id') or session.get('oauth_selling_partner_id')
        
        AmazonConnection.deactivate_selected_for_user(current_user.id)
        AmazonConnection.upsert_for_marketplace(current_user.id, marketplace_id, {
            'seller_id': selling_partner_id or 'pending',
            'marketplace_name': marketplace_name,
            'refresh_token_encrypted': encryption.encrypt(token_data['refresh_token']),
            'access_token_encrypted': encryption.encrypt(token_data.get('access_token')),
            'token_expires_at': datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in else None,
            'is_active': True,
            'is_selected': True,
        })
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        session.pop('oauth_init_state', None)
        session.pop('oauth_marketplace_id', None)
        session.pop('oauth_marketplace_name', None)
        session.pop('oauth_selling_partner_id', None)
        
        flash('Amazon account connected successfully!', 'success')
        return redirect(url_for('dashboard.amazon_settings'))
        
    except Exception as e:
        flash(f'Failed to connect Amazon account: {str(e)}', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/amazon/disconnect', methods=['POST'])
@login_required
def amazon_disconnect():
    """Disconnect Amazon account"""
    marketplace_id = request.form.get('marketplace_id', '').strip()
    collection = AmazonConnection.get_collection()
    was_selected = False
    if marketplace_id:
        existing = collection.find_one({'user_id': current_user.id, 'marketplace_id': marketplace_id, 'is_active': True})
        was_selected = bool(existing and existing.get('is_selected'))
    query = {'user_id': current_user.id, 'is_active': True}
    if marketplace_id:
        query['marketplace_id'] = marketplace_id

    result = collection.update_many(
        query,
        {'$set': {'is_active': False}}
    )
    
    if result.modified_count > 0:
        if was_selected:
            fallback = collection.find_one({'user_id': current_user.id, 'is_active': True})
            if fallback:
                collection.update_one({'_id': fallback['_id']}, {'$set': {'is_selected': True}})
        flash('Amazon account disconnected.', 'info')
    else:
        flash('No Amazon account connected.', 'warning')
    
    return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/amazon/direct-connect', methods=['POST'])
@login_required
def amazon_direct_connect():
    """Connect account using a self-authorized refresh token."""
    refresh_token = request.form.get('refresh_token', '').strip()
    seller_id = request.form.get('seller_id', '').strip()
    marketplace_id = request.form.get('marketplace_id', 'A21TJRUUN4KGV').strip()

    if not refresh_token:
        flash('Refresh token is required', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))

    if not seller_id:
        flash('Seller ID is required', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))

    try:
        encryption = TokenEncryption()
        AmazonConnection.deactivate_selected_for_user(current_user.id)
        AmazonConnection.upsert_for_marketplace(current_user.id, marketplace_id, {
            'seller_id': seller_id,
            'marketplace_name': AmazonOAuth.get_marketplace_name(marketplace_id),
            'refresh_token_encrypted': encryption.encrypt(refresh_token),
            'access_token_encrypted': None,
            'token_expires_at': None,
            'is_active': True,
            'is_selected': True,
        })

        flash(f'Amazon account connected successfully for {AmazonOAuth.get_marketplace_name(marketplace_id)}.', 'success')
    except Exception as e:
        flash(f'Failed to connect Amazon account: {str(e)}', 'danger')

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
    marketplace_id = request.form.get('marketplace_id', '').strip()
    query = {'user_id': current_user.id, 'is_active': True}
    if marketplace_id:
        query['marketplace_id'] = marketplace_id
    else:
        query['is_selected'] = True

    result = collection.find_one_and_update(
        query,
        {'$set': {'seller_id': seller_id, 'updated_at': datetime.now(UTC)}}
    )
    
    if result:
        flash('Seller ID updated successfully', 'success')
    else:
        flash('No active Amazon connection found', 'danger')
    
    return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/amazon/select-marketplace', methods=['POST'])
@login_required
def select_marketplace():
    """Switch the currently selected marketplace connection."""
    marketplace_id = request.form.get('marketplace_id', '').strip()
    if not marketplace_id:
        flash('Marketplace is required', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))

    connection = current_user.get_active_connection(marketplace_id=marketplace_id)
    if not connection:
        flash('Marketplace connection not found', 'danger')
        return redirect(url_for('dashboard.amazon_settings'))

    AmazonConnection.deactivate_selected_for_user(current_user.id)
    AmazonConnection.get_collection().update_one(
        {'_id': connection._id},
        {'$set': {'is_selected': True, 'updated_at': datetime.now(UTC)}}
    )
    flash(f'{connection.marketplace_name} is now your active marketplace.', 'success')
    return redirect(url_for('dashboard.amazon_settings'))


@bp.route('/invites', methods=['POST'])
@login_required
def create_invite():
    """Create an email invitation that gates account registration."""
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Invite email is required', 'danger')
        return redirect(url_for('dashboard.team_access'))

    existing_user = User.find_by_email(email)
    if existing_user:
        flash('That email already has an account', 'warning')
        return redirect(url_for('dashboard.team_access'))

    invite = Invitation({
        'email': email,
        'invited_by_user_id': current_user.id,
    }).save()
    invite_url = url_for('auth.register', invite=invite.token, _external=True)

    try:
        sent = _send_invite_email(email, invite_url)
    except Exception as exc:
        current_app.logger.exception("Failed to send invite email")
        flash(f'Invite created, but email sending failed: {exc}', 'warning')
        flash(f'Share this invite link manually: {invite_url}', 'info')
        return redirect(url_for('dashboard.team_access'))

    if sent:
        flash(f'Invite sent to {email}', 'success')
    else:
        flash(f'Invite created for {email}. Configure SMTP to send automatically.', 'warning')
        flash(f'Share this invite link manually: {invite_url}', 'info')

    return redirect(url_for('dashboard.team_access'))
