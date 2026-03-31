"""
Listing Service - High-level listing operations (MongoDB Version)
"""

from datetime import UTC, datetime

from flask import current_app

from app import mongo
from app.services.sp_api import SPAPIClient


class ListingService:
    """
    High-level service for listing operations
    Handles business logic and database logging
    """

    def __init__(self, user):
        self.user = user
        self.connection = user.get_active_connection()
        self.connections = user.get_amazon_connections()
        self._sku_connection_cache = {}
        if self.connection:
            current_app.logger.info(
                f"ListingService: Connection found - Marketplace: {self.connection.marketplace_id}"
            )
        else:
            current_app.logger.warning("ListingService: No active connection found")
        self.client = SPAPIClient(connection=self.connection) if self.connection else None

    def _client_for_connection(self, connection):
        return SPAPIClient(connection=connection) if connection else None

    def _connected_accounts(self):
        return self.connections or []

    def _get_connection_by_id(self, connection_id):
        if not connection_id:
            return None
        return self.user.get_connection_by_id(connection_id)

    def _resolve_connection_for_sku(self, sku, preferred_connection_id=None):
        """Find the connected seller account that owns the given SKU."""
        if not sku:
            raise Exception("SKU is required")

        preferred_connection = self._get_connection_by_id(preferred_connection_id)
        if preferred_connection:
            try:
                client = self._client_for_connection(preferred_connection)
                client.get_listings_item(preferred_connection.seller_id, sku)
                self._sku_connection_cache[sku] = preferred_connection
                return preferred_connection
            except Exception as exc:
                current_app.logger.info(
                    "Preferred connection %s could not load SKU %s: %s",
                    preferred_connection.id,
                    sku,
                    exc,
                )

        cached = self._sku_connection_cache.get(sku)
        if cached:
            return cached

        connections = self._connected_accounts()
        if not connections:
            raise Exception("Amazon account not connected")

        last_error = None
        for connection in connections:
            try:
                client = self._client_for_connection(connection)
                client.get_listings_item(connection.seller_id, sku)
                self._sku_connection_cache[sku] = connection
                return connection
            except Exception as exc:
                last_error = exc
                current_app.logger.info(
                    "SKU %s not found for seller %s in marketplace %s: %s",
                    sku,
                    connection.seller_id,
                    connection.marketplace_id,
                    exc,
                )

        if last_error:
            raise last_error
        raise Exception(f"SKU '{sku}' not found in any connected seller account")

    def is_connected(self):
        """Check if user has any Amazon connection."""
        return bool(self._connected_accounts())

    def search_items(self, keywords=None, asins=None, page_size=20):
        """Search catalog items across all connected seller accounts."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        aggregated = []
        seen = set()
        failures = []

        for connection in self._connected_accounts():
            try:
                client = self._client_for_connection(connection)
                if asins:
                    result = client.search_catalog_items(
                        identifiers=asins,
                        identifier_type='ASIN',
                        page_size=page_size,
                    )
                else:
                    result = client.search_catalog_items(
                        keywords=keywords,
                        page_size=page_size,
                    )

                for item in result.get('items', []):
                    formatted = self._format_catalog_item(
                        item,
                        connection=connection,
                    )
                    dedupe_key = (
                        formatted.get('asin'),
                        connection.marketplace_id,
                        connection.seller_id,
                    )
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    aggregated.append(formatted)
            except Exception as exc:
                failures.append(f"{connection.marketplace_name}/{connection.seller_id}: {exc}")
                current_app.logger.warning(
                    "Catalog search failed for %s / %s: %s",
                    connection.marketplace_name,
                    connection.seller_id,
                    exc,
                )

        if aggregated:
            return aggregated

        if failures:
            raise Exception(" ; ".join(failures))
        return []

    def get_item_details(self, asin, connection_id=None):
        """Get detailed catalog item information across connected accounts."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        failures = []
        connections = self._connected_accounts()
        if connection_id:
            specific = self.user.get_connection_by_id(connection_id)
            connections = [specific] if specific else []

        for connection in connections:
            try:
                client = self._client_for_connection(connection)
                result = client.get_catalog_item(asin)
                return self._format_catalog_item(result, detailed=True, connection=connection)
            except Exception as exc:
                failures.append(f"{connection.marketplace_name}/{connection.seller_id}: {exc}")
                current_app.logger.warning(
                    "Catalog item lookup failed for %s / %s / %s: %s",
                    connection.marketplace_name,
                    connection.seller_id,
                    asin,
                    exc,
                )

        if failures:
            raise Exception(" ; ".join(failures))
        raise Exception(f"ASIN '{asin}' not found in any connected seller account")

    def get_listing_by_sku(self, sku, connection_id=None):
        """Get listing details by seller SKU."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        try:
            connection = self._resolve_connection_for_sku(sku, preferred_connection_id=connection_id)
            client = self._client_for_connection(connection)
            result = client.get_listings_item(connection.seller_id, sku)
            formatted = self._format_listing_item(result)
            formatted["resolved_connection"] = {
                "seller_id": connection.seller_id,
                "marketplace_id": connection.marketplace_id,
                "marketplace_name": connection.marketplace_name,
                "connection_id": connection.id,
            }
            return formatted
        except Exception as e:
            current_app.logger.error(f"Get listing failed: {e}")
            raise

    def update_price(self, sku, price, currency='INR', sale_price=None, connection_id=None):
        """Update product price."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        log_id = self._create_log(
            sku=sku,
            operation='UPDATE_PRICE',
            payload={
                'sku': sku,
                'price': price,
                'currency': currency,
                'sale_price': sale_price,
            },
        )

        try:
            connection = self._resolve_connection_for_sku(sku, preferred_connection_id=connection_id)
            client = self._client_for_connection(connection)
            product_type = self.resolve_product_type_for_sku(sku, connection_id=connection.id)
            result = client.update_price(
                connection.seller_id,
                sku,
                price,
                currency,
                sale_price,
                product_type=product_type,
            )
            self._mark_log_success(log_id, result)
            return result
        except Exception as e:
            self._mark_log_failed(log_id, e)
            raise

    def update_content(self, sku, data, connection_id=None):
        """Update listing content (title, description, bullets, search terms)."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        log_id = self._create_log(
            sku=sku,
            operation='UPDATE_CONTENT',
            payload=data,
        )

        try:
            connection = self._resolve_connection_for_sku(sku, preferred_connection_id=connection_id)
            client = self._client_for_connection(connection)
            product_type = self.resolve_product_type_for_sku(sku, connection_id=connection.id)
            patches = []

            if 'title' in data:
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/item_name',
                    'value': [{'value': data['title'], 'marketplace_id': connection.marketplace_id}],
                })

            if 'description' in data:
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/product_description',
                    'value': [{'value': data['description'], 'marketplace_id': connection.marketplace_id}],
                })

            if 'bullet_points' in data:
                bullets = [
                    {'value': bullet, 'marketplace_id': connection.marketplace_id}
                    for bullet in data['bullet_points']
                ]
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/bullet_point',
                    'value': bullets,
                })

            if 'search_terms' in data:
                terms = [{'value': ' '.join(data['search_terms']), 'marketplace_id': connection.marketplace_id}]
                patches.append({
                    'op': 'replace',
                    'path': '/attributes/generic_keyword',
                    'value': terms,
                })

            result = client.patch_listings_item(
                connection.seller_id,
                sku,
                patches,
                product_type=product_type,
            )
            self._mark_log_success(log_id, result)
            return result
        except Exception as e:
            self._mark_log_failed(log_id, e)
            raise

    def update_attributes(self, sku, data, connection_id=None):
        """Update arbitrary top-level listing attributes."""
        if not self.is_connected():
            raise Exception("Amazon account not connected")

        log_id = self._create_log(
            sku=sku,
            operation='UPDATE_ATTRIBUTES',
            payload=data,
        )

        try:
            connection = self._resolve_connection_for_sku(sku, preferred_connection_id=connection_id)
            client = self._client_for_connection(connection)
            product_type = self.resolve_product_type_for_sku(sku, connection_id=connection.id)
            patches = []
            for attribute_name, attribute_value in data.items():
                patches.append({
                    'op': 'replace',
                    'path': f'/attributes/{attribute_name}',
                    'value': attribute_value,
                })

            result = client.patch_listings_item(
                connection.seller_id,
                sku,
                patches,
                product_type=product_type,
            )
            self._mark_log_success(log_id, result)
            return result
        except Exception as e:
            self._mark_log_failed(log_id, e)
            raise

    def resolve_product_type_for_sku(self, sku, connection_id=None):
        """Use the live listing product type when available, otherwise fall back to PRODUCT."""
        try:
            listing = self.get_listing_by_sku(sku, connection_id=connection_id)
        except Exception:
            return 'PRODUCT'

        product_type = listing.get('product_type') or 'PRODUCT'
        return product_type if product_type != 'N/A' else 'PRODUCT'

    def get_product_requirements_guide(self, product_type):
        """Return a lightweight guide for required and recommended attributes."""
        if not self.is_connected() or not product_type or product_type == 'N/A':
            return None

        try:
            client = self.client
            if not client and self._connected_accounts():
                client = self._client_for_connection(self._connected_accounts()[0])
            definition = client.get_product_type_definition(product_type)
        except Exception as exc:
            current_app.logger.warning(f"Could not load product type definition for {product_type}: {exc}")
            return None

        schema = client.get_product_type_schema(definition) or {}
        properties = schema.get('properties') or {}

        required_attributes = list(schema.get('required') or [])
        browse_attributes = [
            key for key in properties.keys()
            if 'browse' in key.lower() or 'rbn' in key.lower()
        ]
        recommended_attributes = [
            key for key, value in properties.items()
            if isinstance(value, dict) and key not in required_attributes and key not in browse_attributes
        ]

        return {
            'product_type': product_type,
            'requirements': definition.get('requirements') or 'LISTING',
            'requirements_enforced': definition.get('requirementsEnforced') or 'ENFORCED',
            'property_groups': definition.get('propertyGroups') or {},
            'property_names': definition.get('propertyNames') or [],
            'required_attributes': required_attributes[:20],
            'recommended_attributes': recommended_attributes[:20],
            'browse_attributes': browse_attributes[:10],
        }

    def _create_log(self, sku, operation, payload):
        log_data = {
            'user_id': self.user.id,
            'sku': sku,
            'operation': operation,
            'status': 'PENDING',
            'request_payload': payload,
            'created_at': datetime.now(UTC),
        }
        return mongo.db.update_logs.insert_one(log_data).inserted_id

    def _mark_log_success(self, log_id, result):
        mongo.db.update_logs.update_one(
            {'_id': log_id},
            {'$set': {
                'status': 'SUCCESS',
                'response_payload': result,
                'completed_at': datetime.now(UTC),
            }}
        )

    def _mark_log_failed(self, log_id, error):
        mongo.db.update_logs.update_one(
            {'_id': log_id},
            {'$set': {
                'status': 'FAILED',
                'error_message': str(error),
                'completed_at': datetime.now(UTC),
            }}
        )

    def _format_catalog_item(self, item, detailed=False, connection=None):
        """Format catalog item for display."""
        attributes = item.get('attributes', {})
        summaries = item.get('summaries', [{}])[0] if item.get('summaries') else {}
        images = item.get('images', [{}])[0] if item.get('images') else {}

        main_image = None
        if images and 'images' in images:
            for image in images['images']:
                if image.get('variant') == 'MAIN':
                    main_image = image.get('link')
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
            'browse_classifications': item.get('classifications') or [],
        }

        if connection:
            formatted['resolved_connection'] = {
                'seller_id': connection.seller_id,
                'marketplace_id': connection.marketplace_id,
                'marketplace_name': connection.marketplace_name,
                'connection_id': connection.id,
            }

        if detailed:
            description_attr = attributes.get('product_description') or [{}]
            formatted['description'] = description_attr[0].get('value', '') or ''
            formatted['bullet_points'] = [
                bullet.get('value') for bullet in (attributes.get('bullet_point') or []) if bullet.get('value')
            ]
            formatted['images'] = images.get('images', [])

        return formatted

    def _format_listing_item(self, item):
        """Format listing item for display."""
        attributes = item.get('attributes', {})
        summaries = item.get('summaries', [{}])[0] if item.get('summaries') else {}
        offers = item.get('offers', [])

        price_info = {}
        if offers:
            offer = offers[0]
            price_info = {
                'price': offer.get('price', {}).get('amount'),
                'currency': offer.get('price', {}).get('currencyCode'),
            }

        return {
            'sku': item.get('sku'),
            'asin': item.get('asin'),
            'title': summaries.get('itemName', 'N/A'),
            'status': summaries.get('status', []),
            'price': price_info,
            'issues': item.get('issues', []),
            'attributes': attributes,
            'product_type': summaries.get('productType', 'N/A'),
        }
