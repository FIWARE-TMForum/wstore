# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

import base64
import os
from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from wstore.models import Resource, ResourcePlugin, Context
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.rollback import rollback
from wstore.store_commons.utils.name import is_valid_file
from wstore.store_commons.utils.url import is_valid_url


class AssetManager:

    def __init__(self):
        pass

    def _save_resource_file(self, provider, file_):
        # Load file contents
        if isinstance(file_, dict):
            file_name = file_['name']
            content = base64.b64decode(file_['data'])
        else:
            file_name = file_.name
            file_.seek(0)
            content = file_.read()

        # Check file name
        if not is_valid_file(file_name):
            raise ValueError('Invalid file name format: Unsupported character')

        # Create provider dir for assets if it does not exists
        provider_dir = os.path.join(settings.MEDIA_ROOT, 'assets', provider)

        if not os.path.isdir(provider_dir):
            os.mkdir(provider_dir)

        file_path = os.path.join(provider_dir, file_name)
        resource_path = file_path[file_path.index(settings.MEDIA_DIR):]

        if resource_path.startswith('/'):
            resource_path = resource_path[1:]

        # Check if the file already exists
        if os.path.exists(file_path):
            res = Resource.objects.get(resource_path=resource_path)
            if res.product_id is not None:
                # If the resource has state field, it means that a product
                # spec has been created, so it cannot be overridden
                raise ConflictError('The provided digital asset (' + file_name + ') already exists')
            res.delete()

        # Create file
        with open(file_path, "wb") as f:
            f.write(content)

        self.rollback_logger['files'].append(file_path)

        site = Context.objects.all()[0].site.domain
        return resource_path, urljoin(site, '/charging/' + resource_path)

    def _create_resource_model(self, provider, resource_data):
        # Create the resource
        resource = Resource.objects.create(
            provider=provider,
            version=resource_data['version'],
            download_link=resource_data['link'],
            resource_path=resource_data['content_path'],
            content_type=resource_data['content_type'].lower(),
            resource_type=resource_data['resource_type'],
            state=resource_data['state'],
            is_public=resource_data['is_public'],
            meta_info=resource_data['metadata']
        )
        self.rollback_logger['models'].append(resource)

        return resource

    def _validate_asset_type(self, resource_type, content_type, provided_as, metadata):

        if not resource_type and metadata:
            raise ValueError('You have to specify a valid asset type for providing meta data')

        if not resource_type:
            return

        plugins = ResourcePlugin.objects.filter(name=resource_type)
        if not len(plugins):
            raise ObjectDoesNotExist('The asset type ' + resource_type + ' does not exists')

        asset_type = plugins[0]

        # Validate content type
        if len(asset_type.media_types) and content_type not in asset_type.media_types:
            raise ValueError('The content type ' + content_type + ' is not valid for the specified asset type')

        # Validate providing method
        if provided_as not in asset_type.formats:
            raise ValueError(
                'The format used for providing the digital asset (' +
                provided_as + ') is not valid for the given asset type')

        # Validate that the included metadata is valid according to the form field
        if metadata and not asset_type.form:
            raise ValueError('The specified asset type does not allow meta data')

        if asset_type.form:

            for k, v in asset_type.form.iteritems():
                # Validate mandatory fields
                if 'mandatory' in v and v['mandatory'] and 'default' not in v and k not in metadata:
                    raise ValueError('Missing mandatory field ' + k + ' in metadata')

                # Validate metadata types
                if k in metadata and v['type'] != 'checkbox' and not (isinstance(metadata[k], str) or isinstance(metadata[k], unicode)):
                    raise TypeError('Metadata field ' + k + ' must be a string')

                if k in metadata and v['type'] == 'checkbox' and not isinstance(metadata[k], bool):
                    raise TypeError('Metadata field ' + k + ' must be a boolean')

                if k in metadata and v['type'] == 'select' and metadata[k].lower() not in [option['value'].lower() for option in v['options']]:
                    raise ValueError('Metadata field ' + k + ' value is not one of the available options')

                # Include default values
                if k not in metadata and 'default' in v:
                    metadata[k] = v['default']

    def _load_resource_info(self, provider, data, file_=None):

        resource_data = {
            'content_type': data['contentType'],
            'version': '',
            'resource_type': data.get('resourceType', ''),
            'state': '',
            'is_public': data.get('isPublic', False),
            'content_path': ''
        }

        current_organization = provider.userprofile.current_organization

        resource_data['metadata'] = data.get('metadata', {})

        # Check if the asset is a file upload or a service registration
        provided_as = 'FILE'
        if 'content' in data:
            if isinstance(data['content'], str) or isinstance(data['content'], unicode):
                # Check that the download link is not already being used
                existing_assets = Resource.objects.filter(download_link=data['content'], provider=current_organization)
                is_conflict = False
                for asset in existing_assets:
                    if asset.product_id is not None:
                        is_conflict = True
                    else:
                        asset.delete()

                if is_conflict:
                    raise ConflictError('The provided digital asset already exists')

                download_link = data['content']
                provided_as = 'URL'

            elif isinstance(data['content'], dict):
                resource_data['content_path'], download_link = \
                    self._save_resource_file(current_organization.name, data['content'])

            else:
                raise TypeError('content field has an unsupported type, expected string or object')

        elif file_ is not None:
            resource_data['content_path'], download_link = self._save_resource_file(current_organization.name, file_)

        else:
            raise ValueError('The digital asset has not been provided')

        if not is_valid_url(download_link):
            raise ValueError('The provided content is not a valid URL')

        resource_data['link'] = download_link

        # Validate asset according to its type
        self._validate_asset_type(
            resource_data['resource_type'], resource_data['content_type'], provided_as, resource_data['metadata'])

        return resource_data, current_organization

    @rollback()
    def upload_asset(self, provider, data, file_=None):
        """
        Uploads a new digital asset that will be used to create a product Specification
        :param provider: User uploading the digital asset
        :param data: Information of the asset
        :param file_: Digital asset file, in case it has been provided as multipart/form-data
        :return: The href of the digital asset
        """

        if 'contentType' not in data:
            raise ValueError('Missing required field: contentType')

        resource_data, current_organization = self._load_resource_info(provider, data, file_=file_)
        resource = self._create_resource_model(current_organization, resource_data)

        return resource

    def get_resource_info(self, resource):
        return {
            'id': resource.pk,
            'version': resource.version,
            'contentType': resource.content_type,
            'state': resource.state,
            'href': resource.get_uri(),
            'location': resource.get_url(),
            'resourceType': resource.resource_type,
            'metadata': resource.meta_info
        }

    def get_asset_info(self, asset_id):
        try:
            asset = Resource.objects.get(pk=asset_id)
        except:
            raise ObjectDoesNotExist('The specified digital asset does not exists')

        return self.get_resource_info(asset)

    def get_product_assets(self, product_id):
        assets = Resource.objects.filter(product_id=product_id)

        return [self.get_resource_info(asset) for asset in assets]

    def get_provider_assets_info(self, provider, pagination=None):

        if pagination and ('offset' not in pagination or 'size' not in pagination):
            raise ValueError('Missing required parameter in pagination')

        if pagination and (not int(pagination['offset']) >= 0 or not int(pagination['size']) > 0):
            raise ValueError('Invalid pagination limits')

        response = []

        resources = Resource.objects.filter(provider=provider.current_organization)

        if pagination:
            x = int(pagination['offset'])
            y = x + int(pagination['size'])

            resources = resources[x:y]

        for res in resources:
            response.append(self.get_resource_info(res))

        return response
