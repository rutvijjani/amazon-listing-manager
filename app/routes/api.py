"""
API Routes - AJAX endpoints
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.listing_service import ListingService
from app.models import UpdateLog, BulkUpdateJob

bp = Blueprint('api', __name__)


@bp.route('/search-items')
@login_required
def search_items():
    """API endpoint to search items"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        return jsonify({'error': 'Amazon account not connected'}), 400
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'keyword')
    
    if not query:
        return jsonify({'items': []})
    
    try:
        if search_type == 'asin':
            asins = [a.strip() for a in query.split(',')]
            items = service.search_items(asins=asins)
        else:
            items = service.search_items(keywords=query)
        
        return jsonify({'items': items, 'count': len(items)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/item/<asin>')
@login_required
def get_item(asin):
    """API endpoint to get item details"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        return jsonify({'error': 'Amazon account not connected'}), 400
    
    try:
        item = service.get_item_details(asin)
        return jsonify(item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/listing/<sku>')
@login_required
def get_listing(sku):
    """API endpoint to get listing by SKU"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        return jsonify({'error': 'Amazon account not connected'}), 400
    
    try:
        listing = service.get_listing_by_sku(sku)
        return jsonify(listing)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/update-price', methods=['POST'])
@login_required
def update_price():
    """API endpoint to update price"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        return jsonify({'error': 'Amazon account not connected'}), 400
    
    data = request.get_json()
    
    try:
        log = service.update_price(
            sku=data.get('sku'),
            price=float(data.get('price', 0)),
            currency=data.get('currency', 'INR'),
            sale_price=float(data.get('sale_price')) if data.get('sale_price') else None
        )
        
        return jsonify({
            'success': True,
            'log_id': log.id,
            'status': log.status
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/update-inventory', methods=['POST'])
@login_required
def update_inventory():
    """API endpoint to update inventory"""
    service = ListingService(current_user)
    
    if not service.is_connected():
        return jsonify({'error': 'Amazon account not connected'}), 400
    
    data = request.get_json()
    
    try:
        log = service.update_inventory(
            sku=data.get('sku'),
            quantity=int(data.get('quantity', 0)),
            fulfillment_channel=data.get('fulfillment_channel', 'DEFAULT')
        )
        
        return jsonify({
            'success': True,
            'log_id': log.id,
            'status': log.status
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/stats')
@login_required
def get_stats():
    """Get dashboard stats"""
    stats = {
        'total_updates': UpdateLog.query.filter_by(user_id=current_user.id).count(),
        'successful': UpdateLog.query.filter_by(user_id=current_user.id, status='SUCCESS').count(),
        'failed': UpdateLog.query.filter_by(user_id=current_user.id, status='FAILED').count(),
        'pending': UpdateLog.query.filter_by(user_id=current_user.id, status='PENDING').count(),
    }
    
    return jsonify(stats)


@bp.route('/recent-logs')
@login_required
def recent_logs():
    """Get recent update logs"""
    logs = UpdateLog.query.filter_by(user_id=current_user.id)\
        .order_by(UpdateLog.created_at.desc())\
        .limit(10).all()
    
    return jsonify([{
        'id': log.id,
        'asin': log.asin,
        'sku': log.sku,
        'operation': log.operation,
        'status': log.status,
        'created_at': log.created_at.isoformat() if log.created_at else None,
        'error_message': log.error_message
    } for log in logs])


@bp.route('/job-status/<int:job_id>')
@login_required
def job_status(job_id):
    """Get bulk job status"""
    job = BulkUpdateJob.query.filter_by(id=job_id, user_id=current_user.id).first()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'id': job.id,
        'status': job.status,
        'total': job.total_records,
        'processed': job.processed_records,
        'success': job.success_count,
        'failed': job.failed_count,
        'progress': (job.processed_records / job.total_records * 100) if job.total_records else 0
    })
