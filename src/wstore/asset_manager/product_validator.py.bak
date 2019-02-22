# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

# This file belongs to the business-charging-backend
# of the Business API Ecosystem.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.asset_manager.models import ResourcePlugin, Resource
from wstore.asset_manager.errors import ProductError
from wstore.asset_manager.inventory_upgrader import InventoryUpgrader
from wstore.asset_manager.resource_plugins.decorators import on_product_spec_validation, on_product_spec_attachment, on_product_spec_upgrade
from wstore.asset_manager.catalog_validator import CatalogValidator
from wstore.store_commons.database import DocumentLock
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.version import is_valid_version, is_lower_version
from wstore.store_commons.rollback import rollback, downgrade_asset_pa, downgrade_asset


class ProductValidator(CatalogValidator):

    def _get_asset_resouces(self, asset_t, url):
        # Search the asset type
        asset_type = ResourcePlugin.objects.get(name=asset_t)

        # Validate location format
        if not is_valid_url(url):
            raise ProductError('The location characteristic included in the product specification is not a valid URL')

        # Use the location to retrieve the attached asset
        assets = Resource.objects.filter(download_link=url)

        return asset_type, assets

    def _validate_product_characteristics(self, asset, provider, asset_t, media_type):
        if asset.provider != provider:
            raise PermissionDenied('You are not authorized to use the digital asset specified in the location characteristic')

        if asset.resource_type != asset_t:
            raise ProductError('The specified asset type is different from the asset one')

        if asset.content_type.lower() != media_type.lower():
            raise ProductError('The provided media type characteristic is different from the asset one')

        if asset.is_public:
            raise ProductError('It is not allowed to create products with public assets')

    @on_product_spec_validation
    def _validate_product(self, provider, asset_t, media_type, url):

        asset_type, assets = self._get_asset_resouces(asset_t, url)

        if len(assets):
            # The asset is already registered
            asset = assets[0]

            if asset.product_id is not None:
                raise ConflictError('There is already an existing product specification defined for the given digital asset')

            self._validate_product_characteristics(asset, provider, asset_t, media_type)

            asset.has_terms = self._has_terms
            asset.save()
        else:
            # The asset is not yet included, this option is only valid for URL assets without metadata
            site = settings.SITE
            if 'FILE' in asset_type.formats and (('URL' not in asset_type.formats) or
                ('URL' in asset_type.formats and url.startswith(site))):

                raise ProductError('The URL specified in the location characteristic does not point to a valid digital asset')

            if asset_type.form:
                raise ProductError('Automatic creation of digital assets with expected metadata is not supported')

            # Validate media type
            if len(asset_type.media_types) and media_type.lower() not in [media.lower() for media in asset_type.media_types]:
                raise ProductError('The media type characteristic included in the product specification is not valid for the given asset type')

            # Create the new asset model
            asset = Resource.objects.create(
                has_terms=self._has_terms,
                resource_path='',
                download_link=url,
                provider=provider,
                content_type=media_type
            )

        # The asset model is included to the rollback list so if an exception is raised in the plugin post validation
        # the asset model would be deleted
        self.rollback_logger['models'].append(asset)

        return asset

    @on_product_spec_attachment
    def _attach_product_info(self, asset, asset_t, product_spec):
        # Complete asset information
        asset.product_id = product_spec['id']
        asset.version = product_spec['version']
        asset.resource_type = asset_t
        asset.state = 'attached'
        asset.save()

    def _extract_digital_assets(self, bundled_specs):
        assets = []
        for bundled_info in bundled_specs:
            digital_asset = Resource.objects.filter(product_id=bundled_info['id'])
            if len(digital_asset):
                assets.append(digital_asset[0].pk)

        return assets

    def _build_bundle(self, provider, product_spec):
        if 'bundledProductSpecification' not in product_spec or not len(product_spec['bundledProductSpecification']) > 1:
            raise ProductError('A product spec bundle must contain at least two bundled product specs')

        assets = self._extract_digital_assets(product_spec['bundledProductSpecification'])

        if len(assets) and len(assets) != len(product_spec['bundledProductSpecification']):
            raise ProductError('Mixed product bundles are not allowed. All bundled products must be digital or physical')

        if len(assets):
            Resource.objects.create(
                has_terms=self._has_terms,
                resource_path='',
                download_link='',
                provider=provider,
                content_type='bundle',
                bundled_assets=assets
            )

    @rollback()
    def attach_info(self, provider, product_spec):
        # Get the digital asset
        asset_t, media_type, url = self.parse_characteristics(product_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        asset = None
        if is_digital:
            asset = Resource.objects.get(download_link=url)

        elif product_spec['isBundle']:
            # Get the list of bundles pending to be attached of the given provider
            pending_bundles = Resource.objects.filter(
                product_id=None, provider=provider, content_type='bundle', resource_path='', download_link='')

            # Get the digital assets included in the bundle product spec
            assets = self._extract_digital_assets(product_spec['bundledProductSpecification'])

            asset = None
            for bundle in pending_bundles:
                if len(bundle.bundled_assets) == len(assets):

                    for bundled_asset in bundle.bundled_assets:
                        if bundled_asset not in assets:
                            break
                    else:
                        # All the assets are the expected ones, so the bundle is correct
                        asset = bundle

                    if asset is not None:
                        break

        if asset is not None:
            # TODO: Drop the product object from the catalog in case of error
            self.rollback_logger['models'].append(asset)

            # The asset is a digital product or a bundle containing a digital product
            self._attach_product_info(asset, asset_t, product_spec)

    @on_product_spec_upgrade
    def _notify_product_upgrade(self, asset, asset_t, product_spec):
        # Update existing inventory products to include new version asset info
        upgrader = InventoryUpgrader(asset)
        upgrader.start()

        # Set the asset status to attached
        asset.state = 'attached'
        asset.save()

    def _get_upgrading_asset(self, asset_t, url, product_id):
        asset_type, assets = self._get_asset_resouces(asset_t, url)

        if not len(assets):
            raise ProductError('The URL specified in the location characteristic does not point to a valid digital asset')

        asset = assets[0]
        # Lock the access to the asset
        lock = DocumentLock('wstore_resource', asset.pk, 'asset')
        lock.wait_document()

        asset = Resource.objects.get(pk=asset.pk)

        # Check that the asset is in upgrading state
        if asset.state != 'upgrading':
            raise ProductError('There is not a new version of the specified digital asset')

        if asset.product_id != product_id:
            raise ProductError('The specified digital asset is included in other product spec')

        return asset, lock

    def attach_upgrade(self, provider, product_spec):
        asset_t, media_type, url = self.parse_characteristics(product_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        if is_digital:
            asset, lock = self._get_upgrading_asset(asset_t, url, product_spec['id'])
            self._notify_product_upgrade(asset, asset_t, product_spec)

            # Release asset lock
            lock.unlock_document()

    @rollback(downgrade_asset_pa)
    def validate_upgrade(self, provider, product_spec):

        if 'version' in product_spec and 'productSpecCharacteristic' in product_spec:
            # Extract product needed characteristics
            asset_t, media_type, url = self.parse_characteristics(product_spec)
            is_digital = asset_t is not None and media_type is not None and url is not None

            if is_digital:
                asset, lock = self._get_upgrading_asset(asset_t, url, product_spec['id'])

                self._to_downgrade = asset

                self._validate_product_characteristics(asset, provider, asset_t, media_type)

                # Check product version
                if not is_valid_version(product_spec['version']):
                    raise ProductError('The field version does not have a valid format')

                if not is_lower_version(asset.old_versions[-1].version, product_spec['version']):
                    raise ProductError('The provided version is not higher that the previous one')

                # Attach new info
                asset.version = product_spec['version']
                asset.save()

                # Release asset lock
                lock.unlock_document()

    def _rollback_handler(self, provider, product_spec, rollback_method):
        asset_t, media_type, url = self.parse_characteristics(product_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        if is_digital:
            asset_type, assets = self._get_asset_resouces(asset_t, url)

            asset = assets[0]
            self._validate_product_characteristics(asset, provider, asset_t, media_type)
            rollback_method(asset)

    def rollback_create(self, provider, product_spec):
        def rollback_method(asset):
            if asset.product_id is None:
                asset.delete()

        self._rollback_handler(provider, product_spec, rollback_method)

    def rollback_upgrade(self, provider, product_spec):
        def rollback_method(asset):
            if asset.product_id == product_spec['id'] and asset.state == 'upgrading':
                downgrade_asset(asset)

        self._rollback_handler(provider, product_spec, rollback_method)

    @rollback()
    def validate_creation(self, provider, product_spec):
        # Extract product needed characteristics
        asset_t, media_type, url = self.parse_characteristics(product_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        # Product spec bundles are intended for creating composed products, it cannot contain its own asset
        if product_spec['isBundle'] and is_digital:
            raise ProductError('Product spec bundles cannot define digital assets')

        if not product_spec['isBundle'] and is_digital:
            # Process the new digital product
            self._validate_product(provider, asset_t, media_type, url)

        elif product_spec['isBundle'] and not is_digital:
            # The product bundle may contain digital products already registered
            self._build_bundle(provider, product_spec)
