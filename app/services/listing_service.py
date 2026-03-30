"""
Listing Service - High-level listing operations (MongoDB Version)
"""

import json
from datetime import datetime
from flask import current_app
from app.services.sp_api import SPAPIClient
from app.services.auth_service import TokenEncryption
from app import mongo


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
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        # Create log entry
        log_data = {
            'user_id': self.user.id,
            'sku': sku,
            'operation': 'UPDATE_PRICE',
            'status': 'PENDING',
            'request_payload': {
                'sku': sku,
                'price': price,
                'currency': currency,
                'sale_price': sale_price
            },
            'created_at': datetime.utcnow()
        }
        log_id = mongo.db.update_logs.insert_one(log_data).inserted_id
        
        try:
            result = self.client.update_price(
                self.connection.seller_id,
                sku,
                price,
                currency,
                sale_price
            )
            
            # Update log
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'SUCCESS',
                    'response_payload': result,
                    'completed_at': datetime.utcnow()
                }}
            )
            
            return result
            
        except Exception as e:
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'FAILED',
                    'error_message': str(e),
                    'completed_at': datetime.utcnow()
                }}
            )
            raise
    
    def update_inventory(self, sku, quantity, fulfillment_channel='DEFAULT'):
        """
        Update inventory quantity
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        log_data = {
            'user_id': self.user.id,
            'sku': sku,
            'operation': 'UPDATE_INVENTORY',
            'status': 'PENDING',
            'request_payload': {
                'sku': sku,
                'quantity': quantity,
                'fulfillment_channel': fulfillment_channel
            },
            'created_at': datetime.utcnow()
        }
        log_id = mongo.db.update_logs.insert_one(log_data).inserted_id
        
        try:
            result = self.client.update_inventory(
                self.connection.seller_id,
                sku,
                quantity,
                fulfillment_channel
            )
            
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'SUCCESS',
                    'response_payload': result,
                    'completed_at': datetime.utcnow()
                }}
            )
            
            return result
            
        except Exception as e:
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'FAILED',
                    'error_message': str(e),
                    'completed_at': datetime.utcnow()
                }}
            )
            raise
    
    def update_content(self, sku, data):
        """
        Update listing content (title, description, bullets, etc.)
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")
        
        log_data = {
            'user_id': self.user.id,
            'sku': sku,
            'operation': 'UPDATE_CONTENT',
            'status': 'PENDING',
            'request_payload': data,
            'created_at': datetime.utcnow()
        }
        log_id = mongo.db.update_logs.insert_one(log_data).inserted_id
        
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
            
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'SUCCESS',
                    'response_payload': result,
                    'completed_at': datetime.utcnow()
                }}
            )
            
            return result
            
        except Exception as e:
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'FAILED',
                    'error_message': str(e),
                    'completed_at': datetime.utcnow()
                }}
            )
            raise

    def update_attributes(self, sku, data):
        """
        Update arbitrary top-level listing attributes using the JSON structure
        expected by the Listings Items PATCH API.
        """
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        log_data = {
            'user_id': self.user.id,
            'sku': sku,
            'operation': 'UPDATE_ATTRIBUTES',
            'status': 'PENDING',
            'request_payload': data,
            'created_at': datetime.utcnow()
        }
        log_id = mongo.db.update_logs.insert_one(log_data).inserted_id

        try:
            patches = []
            for attribute_name, attribute_value in data.items():
                patches.append({
                    'op': 'replace',
                    'path': f'/attributes/{attribute_name}',
                    'value': attribute_value
                })

            result = self.client.patch_listings_item(
                self.connection.seller_id,
                sku,
                patches
            )

            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'SUCCESS',
                    'response_payload': result,
                    'completed_at': datetime.utcnow()
                }}
            )

            return result

        except Exception as e:
            mongo.db.update_logs.update_one(
                {'_id': log_id},
                {'$set': {
                    'status': 'FAILED',
                    'error_message': str(e),
                    'completed_at': datetime.utcnow()
                }}
            )
            raise
    
    def bulk_update_from_csv(self, csv_data, operation_type):
        """
        Process bulk updates from CSV data
        """
        job_data = {
            'user_id': self.user.id,
            'job_name': f"Bulk {operation_type.title()} Update",
            'total_records': len(csv_data),
            'processed_records': 0,
            'success_count': 0,
            'failed_count': 0,
            'status': 'PROCESSING',
            'started_at': datetime.utcnow(),
            'errors': []
        }
        job_id = mongo.db.bulk_update_jobs.insert_one(job_data).inserted_id
        
        errors = []
        
        for i, row in enumerate(csv_data):
            try:
                sku = row.get('sku')
                if not sku:
                    errors.append({'row': i+1, 'error': 'SKU is required'})
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
                
                mongo.db.bulk_update_jobs.update_one(
                    {'_id': job_id},
                    {'$inc': {'success_count': 1, 'processed_records': 1}}
                )
                
            except Exception as e:
                errors.append({'row': i+1, 'sku': row.get('sku'), 'error': str(e)})
                mongo.db.bulk_update_jobs.update_one(
                    {'_id': job_id},
                    {'$inc': {'failed_count': 1, 'processed_records': 1}}
                )
        
        # Final update
        mongo.db.bulk_update_jobs.update_one(
            {'_id': job_id},
            {'$set': {
                'status': 'COMPLETED' if not errors else 'COMPLETED_WITH_ERRORS',
                'completed_at': datetime.utcnow(),
                'errors': errors
            }}
        )
        
        return job_id
    
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
        
        item_name_attr = attributes.get('item_name') or [{}]
        brand_attr = attributes.get('brand') or [{}]
        product_types = item.get('productTypes') or [{}]

        title = summaries.get('itemName') or item_name_attr[0].get('value') or 'Untitled product'
        brand = summaries.get('brandName') or brand_attr[0].get('value') or 'Unknown'
        product_type = product_types[0].get('productType') if isinstance(product_types, list) and product_types else 'N/A'

        formatted = {
            'asin': item.get('asin') or 'N/A',
            'title': str(title),
            'brand': str(brand),
            'main_image': main_image,
            'product_type': product_type or 'N/A',
            'attributes': attributes,
        }
        
        if detailed:
            description_attr = attributes.get('product_description') or [{}]
            formatted['description'] = description_attr[0].get('value', '') or ''
            formatted['bullet_points'] = [bp.get('value') for bp in (attributes.get('bullet_point') or []) if bp.get('value')]
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
            'issues': item.get('issues', []),
            'attributes': attributes,
            'product_type': summaries.get('productType', 'N/A')
        }
