"""
API Routes - AJAX endpoints for MongoDB
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from bson.errors import InvalidId
from bson.objectid import ObjectId

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
            'log_id': str(log) if log else None,
            'status': 'SUCCESS'
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
            'log_id': str(log) if log else None,
            'status': 'SUCCESS'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/stats')
@login_required
def get_stats():
    """Get dashboard stats"""
    collection = UpdateLog.get_collection()
    stats = {
        'total_updates': collection.count_documents({'user_id': current_user.id}),
        'successful': collection.count_documents({'user_id': current_user.id, 'status': 'SUCCESS'}),
        'failed': collection.count_documents({'user_id': current_user.id, 'status': 'FAILED'}),
        'pending': collection.count_documents({'user_id': current_user.id, 'status': 'PENDING'}),
    }
    
    return jsonify(stats)


@bp.route('/recent-logs')
@login_required
def recent_logs():
    """Get recent update logs"""
    logs = UpdateLog.get_recent_by_user(current_user.id, limit=10)
    
    return jsonify([{
        'id': str(log.get('_id')),
        'asin': log.get('asin'),
        'sku': log.get('sku'),
        'operation': log.get('operation'),
        'status': log.get('status'),
        'created_at': log.get('created_at').isoformat() if log.get('created_at') else None,
        'error_message': log.get('error_message')
    } for log in logs])


@bp.route('/job-status/<job_id>')
@login_required
def job_status(job_id):
    """Get bulk job status"""
    jobs_collection = BulkUpdateJob.get_collection()
    try:
        object_id = ObjectId(job_id)
    except InvalidId:
        return jsonify({'error': 'Invalid job ID'}), 400

    job = jobs_collection.find_one({'_id': object_id, 'user_id': current_user.id})
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    total = job.get('total_records', 0)
    processed = job.get('processed_records', 0)
    
    return jsonify({
        'id': str(job.get('_id')),
        'status': job.get('status'),
        'total': total,
        'processed': processed,
        'success': job.get('success_count', 0),
        'failed': job.get('failed_count', 0),
        'progress': (processed / total * 100) if total else 0
    })
