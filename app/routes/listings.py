"""
Listing Management Routes for MongoDB
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
import csv
import io
import json
from datetime import datetime
from bson.errors import InvalidId
from bson.objectid import ObjectId

from app.services.listing_service import ListingService
from app.models import UpdateLog, BulkUpdateJob

bp = Blueprint('listings', __name__)


def _build_content_payload(form, selected_fields):
    """Build content update payload for only the selected fields."""
    data = {}
    normalized_fields = set(selected_fields or [])

    if 'title' in normalized_fields:
        data['title'] = form.get('title', '').strip()
    if 'description' in normalized_fields:
        data['description'] = form.get('description', '').strip()
    if 'bullet_points' in normalized_fields:
        data['bullet_points'] = [
            bp.strip() for bp in form.get('bullet_points', '').split('\n') if bp.strip()
        ]
    if 'search_terms' in normalized_fields:
        data['search_terms'] = [
            term.strip() for term in form.get('search_terms', '').split(',') if term.strip()
        ]

    return data


def _build_attribute_payload(form):
    """Build generic attribute payload for selected top-level Amazon attributes."""
    payload = {}

    for attribute_key in form.getlist('attribute_keys'):
        mode = form.get(f'attribute_mode__{attribute_key}', 'raw_json')
        original_raw = form.get(f'attribute_original__{attribute_key}', 'null')
        original_value = json.loads(original_raw)

        if mode == 'text':
            entry = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            entry['value'] = (form.get(f'attr_value__{attribute_key}') or '').strip()
            payload[attribute_key] = [entry]
            continue

        if mode == 'number':
            entry = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            raw_value = (form.get(f'attr_value__{attribute_key}') or '').strip()
            if raw_value == '':
                raise Exception(f'Provide a value for attribute "{attribute_key}"')
            entry['value'] = float(raw_value)
            payload[attribute_key] = [entry]
            continue

        if mode == 'boolean':
            entry = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            raw_value = (form.get(f'attr_value__{attribute_key}') or '').strip().lower()
            entry['value'] = raw_value == 'true'
            payload[attribute_key] = [entry]
            continue

        if mode == 'list_text':
            template = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            template.pop('value', None)
            lines = [line.strip() for line in (form.get(f'attr_value__{attribute_key}') or '').splitlines() if line.strip()]
            if not lines:
                raise Exception(f'Provide at least one value for attribute "{attribute_key}"')
            payload[attribute_key] = [{**template, 'value': line} for line in lines]
            continue

        if mode == 'measurement':
            entry = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            raw_value = (form.get(f'attr_value__{attribute_key}') or '').strip()
            if raw_value == '':
                raise Exception(f'Provide a value for attribute "{attribute_key}"')
            entry['value'] = float(raw_value)
            entry['unit'] = (form.get(f'attr_unit__{attribute_key}') or entry.get('unit') or '').strip()
            payload[attribute_key] = [entry]
            continue

        if mode == 'dimensions':
            entry = (original_value or [{}])[0].copy() if isinstance(original_value, list) else {}
            for dim_key in ('length', 'width', 'height'):
                dim_raw = (form.get(f'attr_{dim_key}__{attribute_key}') or '').strip()
                if dim_raw == '':
                    raise Exception(f'Provide {dim_key} for attribute "{attribute_key}"')
                unit = (form.get(f'attr_unit__{attribute_key}') or '').strip()
                dim_entry = entry.get(dim_key, {}).copy()
                dim_entry['value'] = float(dim_raw)
                if unit:
                    dim_entry['unit'] = unit
                entry[dim_key] = dim_entry
            payload[attribute_key] = [entry]
            continue

        textarea_name = f'attr_json__{attribute_key}'
        raw_value = (form.get(textarea_name) or '').strip()
        if not raw_value:
            raise Exception(f'Provide a JSON value for attribute "{attribute_key}"')

        try:
            payload[attribute_key] = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise Exception(f'Invalid JSON for attribute "{attribute_key}": {exc.msg}') from exc

    return payload


def _classify_attribute_editor(attribute_name, attribute_value):
    """Return template metadata for a user-friendly attribute editor."""
    editor = {
        'name': attribute_name,
        'label': attribute_name.replace('_', ' ').replace('-', ' ').title(),
        'mode': 'raw_json',
        'json_value': json.dumps(attribute_value, indent=2),
    }

    if not isinstance(attribute_value, list) or not attribute_value:
        return editor

    if not all(isinstance(item, dict) for item in attribute_value):
        return editor

    first = attribute_value[0]

    if all('value' in item and isinstance(item.get('value'), (str, int, float, bool)) for item in attribute_value):
        if len(attribute_value) == 1:
            value = first.get('value')
            if isinstance(value, bool):
                editor.update({'mode': 'boolean', 'value': value})
            elif isinstance(value, (int, float)):
                editor.update({'mode': 'number', 'value': value})
            else:
                editor.update({'mode': 'text', 'value': value or ''})
        else:
            editor.update({
                'mode': 'list_text',
                'value': '\n'.join(str(item.get('value', '')) for item in attribute_value if item.get('value') is not None),
            })
        return editor

    if len(attribute_value) == 1 and {'value', 'unit'}.issubset(first.keys()) and isinstance(first.get('value'), (int, float)):
        editor.update({
            'mode': 'measurement',
            'value': first.get('value', ''),
            'unit': first.get('unit', ''),
        })
        return editor

    if len(attribute_value) == 1 and all(key in first for key in ('length', 'width', 'height')):
        dimensions = {}
        for dim_key in ('length', 'width', 'height'):
            dim_entry = first.get(dim_key) or {}
            if not isinstance(dim_entry, dict):
                return editor
            dimensions[dim_key] = dim_entry.get('value', '')
        unit = ''
        for dim_key in ('length', 'width', 'height'):
            dim_entry = first.get(dim_key) or {}
            if dim_entry.get('unit'):
                unit = dim_entry.get('unit')
                break
        editor.update({
            'mode': 'dimensions',
            'dimensions': dimensions,
            'unit': unit,
        })
        return editor

    return editor


def _resolve_product_attributes(listing, catalog_item):
    """Resolve loaded product attributes for the advanced attribute editor."""
    if listing and listing.get('attributes'):
        return listing.get('attributes') or {}
    if catalog_item and catalog_item.get('attributes'):
        return catalog_item.get('attributes') or {}
    return {}


def _build_attribute_editors(listing, catalog_item):
    attributes = _resolve_product_attributes(listing, catalog_item)
    return [
        _classify_attribute_editor(attribute_name, attribute_value)
        for attribute_name, attribute_value in sorted(attributes.items())
    ]


@bp.route('/')
@login_required
def index():
    """Listings index page - shows search interface"""
    return render_template('listings/list.html')


@bp.route('/search')
@login_required
def search():
    """Search listings"""
    try:
        service = ListingService(current_user)
        
        if not service.is_connected():
            flash('Please connect your Amazon account first', 'warning')
            return redirect(url_for('dashboard.amazon_settings'))
        
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'keyword')
        
        if not query:
            flash('Please enter a search term', 'warning')
            return render_template('listings/list.html', items=[], query='', search_type=search_type)

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
        current_app.logger.exception("Listing search request failed")
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'keyword')
        flash(f'Search failed: {str(e)}', 'danger')
        return render_template('listings/list.html', items=[], query=query, search_type=search_type)


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


@bp.route('/manual-update', methods=['GET', 'POST'])
@login_required
def manual_update():
    """Manual single-item update, starting from SKU or ASIN."""
    service = ListingService(current_user)

    if not service.is_connected():
        flash('Please connect your Amazon account first', 'warning')
        return redirect(url_for('dashboard.amazon_settings'))

    asin = request.values.get('asin', '').strip()
    sku = request.values.get('sku', '').strip()
    listing = {}
    catalog_item = None
    product_attributes = {}

    if sku:
        try:
            listing = service.get_listing_by_sku(sku)
            asin = asin or (listing.get('asin') or '')
        except Exception as e:
            flash(f'Could not load listing by SKU: {str(e)}', 'warning')
            listing = {'sku': sku, 'asin': asin}

    if asin and not listing.get('title'):
        try:
            catalog_item = service.get_item_details(asin)
        except Exception as e:
            flash(f'Could not load catalog item by ASIN: {str(e)}', 'warning')

    if request.method == 'POST':
        update_type = request.form.get('update_type')
        sku = request.form.get('sku', '').strip()
        asin = request.form.get('asin', '').strip()

        if not sku:
            flash('Seller SKU is required for updates, even when you start from ASIN.', 'danger')
            return render_template(
                'listings/manual_update.html',
                listing=listing,
                catalog_item=catalog_item,
                product_attributes=_resolve_product_attributes(listing, catalog_item),
                attribute_editors=_build_attribute_editors(listing, catalog_item),
                sku=sku,
                asin=asin,
            )

        try:
            if update_type == 'price':
                price = float(request.form.get('price', 0))
                currency = request.form.get('currency', 'INR')
                sale_price = request.form.get('sale_price', '').strip()
                sale_price = float(sale_price) if sale_price else None
                service.update_price(sku, price, currency, sale_price)
                flash('Price updated successfully!', 'success')

            elif update_type == 'inventory':
                quantity = int(request.form.get('quantity', 0))
                channel = request.form.get('fulfillment_channel', 'DEFAULT')
                service.update_inventory(sku, quantity, channel)
                flash('Inventory updated successfully!', 'success')

            elif update_type == 'content':
                selected_fields = request.form.getlist('content_fields')
                if not selected_fields:
                    raise Exception('Select at least one content attribute to update')
                data = _build_content_payload(request.form, selected_fields)
                service.update_content(sku, data)
                flash('Selected content attributes updated successfully!', 'success')

            elif update_type == 'attributes':
                attribute_keys = request.form.getlist('attribute_keys')
                if not attribute_keys:
                    raise Exception('Select at least one product attribute to update')
                data = _build_attribute_payload(request.form)
                service.update_attributes(sku, data)
                flash('Selected product attributes updated successfully!', 'success')

            return redirect(url_for('listings.manual_update', sku=sku, asin=asin))
        except Exception as e:
            current_app.logger.exception("Manual listing update failed")
            flash(f'Update failed: {str(e)}', 'danger')

    return render_template(
        'listings/manual_update.html',
        listing=listing,
        catalog_item=catalog_item,
        product_attributes=_resolve_product_attributes(listing, catalog_item),
        attribute_editors=_build_attribute_editors(listing, catalog_item),
        sku=sku,
        asin=asin,
    )


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
        identifier_type = request.form.get('identifier_type', 'sku')
        content_fields = request.form.getlist('content_fields')
        
        try:
            # Read CSV
            stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
            csv_reader = csv.DictReader(stream)
            csv_data = list(csv_reader)
            
            if not csv_data:
                flash('CSV file is empty', 'danger')
                return redirect(url_for('listings.bulk_update'))

            if operation_type == 'content' and not content_fields:
                flash('Select at least one content attribute for bulk content update', 'danger')
                return redirect(url_for('listings.bulk_update'))
            
            # Create bulk job
            job_id = BulkUpdateJob.create(
                user_id=current_user.id,
                job_name=f"Bulk {operation_type.title()} Update",
                total_records=len(csv_data)
            )
            
            # Process bulk update
            errors = []
            success_count = 0
            failed_count = 0
            
            for i, row in enumerate(csv_data):
                try:
                    asin = (row.get('asin') or '').strip()
                    sku = (row.get('sku') or '').strip()

                    if identifier_type == 'asin' and not asin:
                        errors.append({'row': i+1, 'error': 'ASIN is required'})
                        failed_count += 1
                        continue

                    if not sku:
                        errors.append({
                            'row': i+1,
                            'asin': asin or None,
                            'error': 'SKU is required because Amazon listing updates are seller-SKU based'
                        })
                        failed_count += 1
                        continue
                    
                    if operation_type == 'price':
                        service.update_price(
                            sku,
                            float(row.get('price', 0)),
                            row.get('currency', 'INR'),
                            float(row.get('sale_price')) if row.get('sale_price') else None
                        )
                    
                    elif operation_type == 'inventory':
                        service.update_inventory(
                            sku,
                            int(row.get('quantity', 0)),
                            row.get('fulfillment_channel', 'DEFAULT')
                        )
                    
                    elif operation_type == 'content':
                        data = {}
                        if 'title' in content_fields:
                            data['title'] = (row.get('title') or '').strip()
                        if 'description' in content_fields:
                            data['description'] = (row.get('description') or '').strip()
                        if 'bullet_points' in content_fields:
                            data['bullet_points'] = [bp.strip() for bp in (row.get('bullet_points') or '').split('|') if bp.strip()]
                        if 'search_terms' in content_fields:
                            data['search_terms'] = [term.strip() for term in (row.get('search_terms') or '').split('|') if term.strip()]
                        service.update_content(sku, data)

                    elif operation_type == 'attributes':
                        attributes_json = (row.get('attributes_json') or '').strip()
                        if not attributes_json:
                            raise Exception('attributes_json is required for attributes updates')
                        try:
                            data = json.loads(attributes_json)
                        except json.JSONDecodeError as exc:
                            raise Exception(f'Invalid attributes_json: {exc.msg}') from exc
                        if not isinstance(data, dict):
                            raise Exception('attributes_json must be a JSON object')
                        service.update_attributes(sku, data)
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append({
                        'row': i+1,
                        'asin': row.get('asin'),
                        'sku': row.get('sku'),
                        'error': str(e)
                    })
                    failed_count += 1
            
            # Update job status
            jobs_collection = BulkUpdateJob.get_collection()
            jobs_collection.update_one(
                {'_id': job_id},
                {'$set': {
                    'processed_records': len(csv_data),
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'status': 'COMPLETED' if failed_count == 0 else 'COMPLETED_WITH_ERRORS',
                    'errors': errors,
                    'completed_at': datetime.utcnow()
                }}
            )
            
            if failed_count == 0:
                flash(f'Bulk update completed successfully! {success_count} items updated.', 'success')
            else:
                flash(f'Bulk update completed with {failed_count} errors. {success_count} items updated.', 'warning')
            
            return redirect(url_for('listings.bulk_results', job_id=job_id))
            
        except Exception as e:
            flash(f'Bulk update failed: {str(e)}', 'danger')
            return redirect(url_for('listings.bulk_update'))
    
    recent_jobs = list(
        BulkUpdateJob.get_collection().find({'user_id': current_user.id}).sort('created_at', -1).limit(10)
    )
    return render_template('listings/bulk_update.html', recent_jobs=recent_jobs)


@bp.route('/bulk-results/<job_id>')
@login_required
def bulk_results(job_id):
    """View bulk update results"""
    jobs_collection = BulkUpdateJob.get_collection()
    try:
        object_id = ObjectId(job_id)
    except InvalidId:
        flash('Invalid job ID', 'danger')
        return redirect(url_for('listings.index'))

    job = jobs_collection.find_one({'_id': object_id, 'user_id': current_user.id})
    
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('listings.index'))
    
    return render_template('listings/bulk_results.html', job=job)


@bp.route('/logs')
@login_required
def logs():
    """View update logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    collection = UpdateLog.get_collection()
    logs_list = list(collection.find(
        {'user_id': current_user.id}
    ).sort('created_at', -1).skip((page-1)*per_page).limit(per_page))
    
    total = collection.count_documents({'user_id': current_user.id})
    
    return render_template('listings/logs.html', logs=logs_list, page=page, total=total)


@bp.route('/download-template/<operation_type>')
@login_required
def download_template(operation_type):
    """Download CSV template for bulk upload"""
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
    elif operation_type == 'attributes':
        headers = ['sku', 'attributes_json']
        sample = [
            {'sku': 'SKU001', 'attributes_json': '{"item_name":[{"value":"Updated title","marketplace_id":"A21TJRUUN4KGV"}]}'},
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
