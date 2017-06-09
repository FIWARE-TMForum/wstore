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

from django.core.exceptions import PermissionDenied

from wstore.asset_manager.models import ResourcePlugin, Resource
from wstore.asset_manager.errors import ProductError
from wstore.asset_manager.resource_plugins.decorators import on_product_spec_validation, on_product_spec_attachment
from wstore.asset_manager.catalog_validator import CatalogValidator
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.utils.url import is_valid_url
from wstore.models import Context
from wstore.store_commons.rollback import rollback


class ProductValidator(CatalogValidator):

    @on_product_spec_validation
    def _validate_product(self, provider, asset_t, media_type, url):
        # Search the asset type
        asset_type = ResourcePlugin.objects.get(name=asset_t)

        # Validate location format
        if not is_valid_url(url):
            raise ProductError('The location characteristic included in the product specification is not a valid URL')

        # Use the location to retrieve the attached asset
        assets = Resource.objects.filter(download_link=url)

        if len(assets):
            # The asset is already registered
            asset = assets[0]

            if asset.provider != provider:
                raise PermissionDenied('You are not authorized to use the digital asset specified in the location characteristic')

            if asset.product_id is not None:
                raise ConflictError('There is already an existing product specification defined for the given digital asset')

            if asset.resource_type != asset_t:
                raise ProductError('The specified asset type if different from the asset one')

            if asset.content_type.lower() != media_type.lower():
                raise ProductError('The provided media type characteristic is different from the asset one')

            if asset.is_public:
                raise ProductError('It is not allowed to create products with public assets')

            asset.has_terms = self._has_terms
            asset.save()
        else:
            # The asset is not yet included, this option is only valid for URL assets without metadata
            site = Context.objects.all()[0].site
            if 'FILE' in asset_type.formats and (('URL' not in asset_type.formats) or
                ('URL' in asset_type.formats and url.startswith(site.domain))):

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
        asset.state = product_spec['lifecycleStatus']
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
            self.rollback_logger['models'].append(asset)

            # The asset is a digital product or a bundle containing a digital product
            self._attach_product_info(asset, asset_t, product_spec)

    @rollback()
    def validate_creation(self, provider, product_spec):
        # Extract product needed characteristics
        asset_t, media_type, url = self.parse_characteristics(product_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        # Product spec bundles are intended for create composed products, it cannot contain its own asset
        if product_spec['isBundle'] and is_digital:
            raise ProductError('Product spec bundles cannot define digital assets')

        if not product_spec['isBundle'] and is_digital:
            # Process the new digital product
            self._validate_product(provider, asset_t, media_type, url)

        elif product_spec['isBundle'] and not is_digital:
            # The product bundle may contain digital products already registered
            self._build_bundle(provider, product_spec)
