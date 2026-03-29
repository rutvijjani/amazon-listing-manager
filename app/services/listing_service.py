"""
Listing Service - High-level listing operations
"""

import json
from datetime import datetime
from flask import current_app
from app.services.sp_api import SPAPIClient
from app.services.auth_service import TokenEncryption
from app import db


class ListingService:
    """
    High-level service for listing operations
    Handles business logic and database logging
    """
    
    def __init__(self, user):
        """
        Initialize listing service for a user
        
        Args:
            user: User model instance
        """
        self.user = user
        self.connection = user.get_active_connection()
        if self.connection:
            current_app.logger.info(f"ListingService: Connection found - Marketplace: {self.connection.marketplace_id}")
        else:
            current_app.logger.warning("ListingService: No active connection found")
        self.client = SPAPIClient(connection=self.connection) if self.connection else None
    
    def is_connected(self):
        """Check if user has active Amazon connection"""
        return self.client is not None
    
    def search_items(self, keywords=None, asins=None, page_size=20):
        """
        Search catalog items
        
        Returns:
            List of items with formatted data
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        try:
            if asins:
                # Search by ASINs
                result = self.client.search_catalog_items(
                    identifiers=asins,
                    identifier_type='ASIN',
                    page_size=page_size
                )
            else:
                # Search by keywords
                result = self.client.search_catalog_items(
                    keywords=keywords,
                    page_size=page_size
                )
            
            items = result.get('items', [])
            return [self._format_catalog_item(item) for item in items]
            
        except Exception as e:
            current_app.logger.error(f"Search failed: {e}")
            raise
    
    def get_item_details(self, asin):
        """
        Get detailed item information
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        try:
            result = self.client.get_catalog_item(asin)
            return self._format_catalog_item(result, detailed=True)
        except Exception as e:
            current_app.logger.error(f"Get item failed: {e}")
            raise
    
    def get_listing_by_sku(self, sku):
        """
        Get listing details by seller SKU
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        try:
            result = self.client.get_listings_item(
                self.connection.seller_id,
                sku
            )
            return self._format_listing_item(result)
        except Exception as e:
            current_app.logger.error(f"Get listing failed: {e}")
            raise
    
    def update_price(self, sku, price, currency='INR', sale_price=None):
        """
        Update product price
        
        Returns:
            UpdateLog entry
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        from app.models import UpdateLog
        
        # Create log entry
        log = UpdateLog(
            user_id=self.user.id,
            sku=sku,
            operation='UPDATE_PRICE',
            status='PENDING'
        )
        log.set_request_payload({
            'sku': sku,
            'price': price,
            'currency': currency,
            'sale_price': sale_price
        })
        db.session.add(log)
        db.session.commit()
        
        try:
            result = self.client.update_price(
                self.connection.seller_id,
                sku,
                price,
                currency,
                sale_price
            )
            
            log.mark_success()
            log.set_response_payload(result)
            db.session.commit()
            
            return log
            
        except Exception as e:
            log.mark_failed(str(e))
            db.session.commit()
            raise
    
    def update_inventory(self, sku, quantity, fulfillment_channel='DEFAULT'):
        """
        Update inventory quantity
        
        Returns:
            UpdateLog entry
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        from app.models import UpdateLog
        
        log = UpdateLog(
            user_id=self.user.id,
            sku=sku,
            operation='UPDATE_INVENTORY',
            status='PENDING'
        )
        log.set_request_payload({
            'sku': sku,
            'quantity': quantity,
            'fulfillment_channel': fulfillment_channel
        })
        db.session.add(log)
        db.session.commit()
        
        try:
            result = self.client.update_inventory(
                self.connection.seller_id,
                sku,
                quantity,
                fulfillment_channel
            )
            
            log.mark_success()
            log.set_response_payload(result)
            db.session.commit()
            
            return log
            
        except Exception as e:
            log.mark_failed(str(e))
            db.session.commit()
            raise
    
    def update_content(self, sku, data):
        """
        Update listing content (title, description, bullets, etc.)
        
        Args:
            sku: Product SKU
            data: Dict with content fields
                - title
                - description
                - bullet_points (list)
                - search_terms (list)
        
        Returns:
            UpdateLog entry
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        from app.models import UpdateLog
        
        log = UpdateLog(
            user_id=self.user.id,
            sku=sku,
            operation='UPDATE_CONTENT',
            status='PENDING'
        )
        log.set_request_payload(data)
        db.session.add(log)
        db.session.commit()
        
        try:
            # Build patches for content updates
            patches = []
            
            if 'title' in data:
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/item_name',
                    'value': [{'value': data['title'], 'marketplace_id': self.connection.marketplace_id}]
                })
            
            if 'description' in data:
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/product_description',
                    'value': [{'value': data['description'], 'marketplace_id': self.connection.marketplace_id}]
                })
            
            if 'bullet_points' in data:
                bullets = [{'value': bp, 'marketplace_id': self.connection.marketplace_id} 
                          for bp in data['bullet_points']]
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/bullet_point',
                    'value': bullets
                })
            
            if 'search_terms' in data:
                terms = [{'value': ' '.join(data['search_terms']), 'marketplace_id': self.connection.marketplace_id}]
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/generic_keyword',
                    'value': terms
                })
            
            result = self.client.patch_listings_item(
                self.connection.seller_id,
                sku,
                patches
            )
            
            log.mark_success()
            log.set_response_payload(result)
            db.session.commit()
            
            return log
            
        except Exception as e:
            log.mark_failed(str(e))
            db.session.commit()
            raise
    
    def bulk_update_from_csv(self, csv_data, operation_type):
        """
        Process bulk updates from CSV data
        
        Args:
            csv_data: List of dicts with CSV data
            operation_type: 'price', 'inventory', 'content'
        
        Returns:
            BulkUpdateJob instance
        """
        from app.models import BulkUpdateJob
        
        job = BulkUpdateJob(
            user_id=self.user.id,
            job_name=f"Bulk {operation_type.title()} Update",
            total_records=len(csv_data),
            status='PROCESSING',
            started_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()
        
        errors = []
        
        for i, row in enumerate(csv_data):
            try:
                sku = row.get('sku')
                if not sku:
                    errors.append({'row': i+1, 'error': 'SKU is required'})
                    job.failed_count += 1
                    continue
                
                if operation_type == 'price':
                    self.update_price(
                        sku,
                        float(row.get('price', 0)),
                        row.get('currency', 'INR'),
                        float(row.get('sale_price')) if row.get('sale_price') else None
                    )
                
                elif operation_type == 'inventory':
                    self.update_inventory(
                        sku,
                        int(row.get('quantity', 0)),
                        row.get('fulfillment_channel', 'DEFAULT')
                    )
                
                elif operation_type == 'content':
                    self.update_content(sku, {
                        'title': row.get('title'),
                        'description': row.get('description'),
                        'bullet_points': row.get('bullet_points', '').split('|') if row.get('bullet_points') else None
                    })
                
                job.success_count += 1
                
            except Exception as e:
                errors.append({'row': i+1, 'sku': row.get('sku'), 'error': str(e)})
                job.failed_count += 1
            
            job.processed_records += 1
            db.session.commit()
        
        job.status = 'COMPLETED' if job.failed_count == 0 else 'COMPLETED_WITH_ERRORS'
        job.completed_at = datetime.utcnow()
        if errors:
            job.set_errors(errors)
        db.session.commit()
        
        return job
    
    # ==================== Helper Methods ====================
    
    def _format_catalog_item(self, item, detailed=False):
        """Format catalog item for display"""
        attributes = item.get('attributes', {})
        summaries = item.get('summaries', [{}])[0] if item.get('summaries') else {}
        images = item.get('images', [{}])[0] if item.get('images') else {}
        
        # Get main image
        main_image = None
        if images and 'images' in images:
            for img in images['images']:
                if img.get('variant') == 'MAIN':
                    main_image = img.get('link')
                    break
        
        formatted = {
            'asin': item.get('asin'),
            'title': summaries.get('itemName', attributes.get('item_name', [{}])[0].get('value', 'N/A')),
            'brand': summaries.get('brandName', attributes.get('brand', [{}])[0].get('value', 'N/A')),
            'main_image': main_image,
            'product_type': item.get('productTypes', [{}])[0].get('productType', 'N/A') if item.get('productTypes') else 'N/A',
        }
        
        if detailed:
            formatted['description'] = attributes.get('product_description', [{}])[0].get('value', '')
            formatted['bullet_points'] = [bp.get('value') for bp in attributes.get('bullet_point', [])]
            formatted['images'] = images.get('images', [])
        
        return formatted
    
    def _format_listing_item(self, item):
        """Format listing item for display"""
        attributes = item.get('attributes', {})
        summaries = item.get('summaries', [{}])[0] if item.get('summaries') else {}
        
        # Get price info
        offers = item.get('offers', [])
        price_info = {}
        if offers:
            offer = offers[0]
            price_info = {
                'price': offer.get('price', {}).get('amount'),
                'currency': offer.get('price', {}).get('currencyCode')
            }
        
        # Get inventory
        fulfillment = item.get('fulfillmentAvailability', [])
        inventory = {}
        if fulfillment:
            inv = fulfillment[0]
            inventory = {
                'quantity': inv.get('quantity'),
                'channel': inv.get('fulfillmentChannelCode')
            }
        
        return {
            'sku': item.get('sku'),
            'asin': item.get('asin'),
            'title': summaries.get('itemName', 'N/A'),
            'status': summaries.get('status', []),
            'price': price_info,
            'inventory': inventory,
            'issues': item.get('issues', [])
        }
