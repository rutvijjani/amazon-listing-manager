"""
Listing Management Routes
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
import csv
import io
from app.services.listing_service import ListingService
from app.models import UpdateLog, BulkUpdateJob
from app import db

bp = Blueprint('listings', __name__)


@bp.route('/')
@login_required
def index():
    """Listings index page - shows search interface"""
    return render_template('listings/list.html')


@bp.route('/search')
@login_required
def search():
    """Search listings"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        flash('Please connect your Amazon account first', 'warning')
        return redirect(url_for('dashboard.amazon_settings'))
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'keyword')
    
    if not query:
        flash('Please enter a search term', 'warning')
        return render_template('listings/list.html')
    
    try:
        if search_type == 'asin':
            # Search by ASIN
            asins = [a.strip() for a in query.split(',')]
            items = service.search_items(asins=asins)
        else:
            # Search by keyword
            items = service.search_items(keywords=query)
        
        return render_template('listings/list.html', 
                             items=items, 
                             query=query, 
                             search_type=search_type)
    
    except Exception as e:
        flash(f'Search failed: {str(e)}', 'danger')
        return render_template('listings/list.html', query=query)


@bp.route('/item/<asin>')
@login_required
def item_detail(asin):
    """View item details"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        flash('Please connect your Amazon account first', 'warning')
        return redirect(url_for('dashboard.amazon_settings'))
    
    try:
        item = service.get_item_details(asin)
        return render_template('listings/detail.html', item=item, asin=asin)
    except Exception as e:
        flash(f'Failed to get item details: {str(e)}', 'danger')
        return redirect(url_for('listings.index'))


@bp.route('/edit/<sku>', methods=['GET', 'POST'])
@login_required
def edit(sku):
    """Edit listing by SKU"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        flash('Please connect your Amazon account first', 'warning')
        return redirect(url_for('dashboard.amazon_settings'))
    
    # Get current listing data
    try:
        listing = service.get_listing_by_sku(sku)
    except Exception as e:
        flash(f'Failed to get listing: {str(e)}', 'danger')
        listing = {'sku': sku}
    
    if request.method == 'POST':
        update_type = request.form.get('update_type')
        
        try:
            if update_type == 'price':
                price = float(request.form.get('price', 0))
                currency = request.form.get('currency', 'INR')
                sale_price = request.form.get('sale_price')
                sale_price = float(sale_price) if sale_price else None
                
                service.update_price(sku, price, currency, sale_price)
                flash('Price updated successfully!', 'success')
                
            elif update_type == 'inventory':
                quantity = int(request.form.get('quantity', 0))
                channel = request.form.get('fulfillment_channel', 'DEFAULT')
                
                service.update_inventory(sku, quantity, channel)
                flash('Inventory updated successfully!', 'success')
                
            elif update_type == 'content':
                data = {
                    'title': request.form.get('title'),
                    'description': request.form.get('description'),
                    'bullet_points': [bp.strip() for bp in request.form.get('bullet_points', '').split('\n') if bp.strip()],
                    'search_terms': request.form.get('search_terms', '').split(',')
                }
                
                service.update_content(sku, data)
                flash('Content updated successfully!', 'success')
            
            return redirect(url_for('listings.edit', sku=sku))
            
        except Exception as e:
            flash(f'Update failed: {str(e)}', 'danger')
    
    return render_template('listings/edit.html', listing=listing, sku=sku)


@bp.route('/bulk-update', methods=['GET', 'POST'])
@login_required
def bulk_update():
    """Bulk update via CSV upload"""
    if request.method == 'POST':
        service = ListingService(current_user)
        
        if not service.is_connected():
            flash('Please connect your Amazon account first', 'warning')
            return redirect(url_for('dashboard.amazon_settings'))
        
        # Check file upload
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(url_for('listings.bulk_update'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('listings.bulk_update'))
        
        operation_type = request.form.get('operation_type', 'price')
        
        try:
            # Read CSV
            stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
            csv_reader = csv.DictReader(stream)
            csv_data = list(csv_reader)
            
            if not csv_data:
                flash('CSV file is empty', 'danger')
                return redirect(url_for('listings.bulk_update'))
            
            # Process bulk update
            job = service.bulk_update_from_csv(csv_data, operation_type)
            
            if job.failed_count == 0:
                flash(f'Bulk update completed successfully! {job.success_count} items updated.', 'success')
            else:
                flash(f'Bulk update completed with {job.failed_count} errors. {job.success_count} items updated.', 'warning')
            
            return redirect(url_for('listings.bulk_results', job_id=job.id))
            
        except Exception as e:
            flash(f'Bulk update failed: {str(e)}', 'danger')
            return redirect(url_for('listings.bulk_update'))
    
    return render_template('listings/bulk_update.html')


@bp.route('/bulk-results/<int:job_id>')
@login_required
def bulk_results(job_id):
    """View bulk update results"""
    job = BulkUpdateJob.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    return render_template('listings/bulk_results.html', job=job)


@bp.route('/logs')
@login_required
def logs():
    """View update logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs_query = UpdateLog.query.filter_by(user_id=current_user.id)\
        .order_by(UpdateLog.created_at.desc())
    
    logs = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('listings/logs.html', logs=logs)


@bp.route('/download-template/<operation_type>')
@login_required
def download_template(operation_type):
    """Download CSV template for bulk upload"""
    import csv
    from flask import Response
    
    if operation_type == 'price':
        headers = ['sku', 'price', 'currency', 'sale_price']
        sample = [
            {'sku': 'SKU001', 'price': '999.00', 'currency': 'INR', 'sale_price': '899.00'},
            {'sku': 'SKU002', 'price': '1499.00', 'currency': 'INR', 'sale_price': ''},
        ]
    elif operation_type == 'inventory':
        headers = ['sku', 'quantity', 'fulfillment_channel']
        sample = [
            {'sku': 'SKU001', 'quantity': '100', 'fulfillment_channel': 'DEFAULT'},
            {'sku': 'SKU002', 'quantity': '50', 'fulfillment_channel': 'AMAZON'},
        ]
    elif operation_type == 'content':
        headers = ['sku', 'title', 'description', 'bullet_points']
        sample = [
            {'sku': 'SKU001', 'title': 'Product Title', 'description': 'Product description', 'bullet_points': 'Point 1|Point 2|Point 3'},
        ]
    else:
        flash('Invalid template type', 'danger')
        return redirect(url_for('listings.bulk_update'))
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={operation_type}_template.csv'
        }
    )
