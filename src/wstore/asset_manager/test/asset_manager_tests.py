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

from copy import deepcopy
from mock import MagicMock, mock_open
from nose_parameterized import parameterized

from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings

from wstore.asset_manager import asset_manager
from wstore.asset_manager.test.resource_test_data import *
from wstore.asset_manager import models
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.utils.testing import decorator_mock


class ResourceRetrievingTestCase(TestCase):

    tags = ('asset-manager', )

    def _mock_resource(self, info, provider):
        # Mock resource model
        resource = MagicMock()
        resource.pk = info['pk']
        resource.provider = provider
        resource.version = info['version']
        resource.content_type = info['content_type']
        resource.state = info['state']
        resource.download_link = info['download_link']
        resource.resource_type = info['type']
        resource.meta_info = {}

        resource.get_url.return_value = info['download_link']
        resource.get_uri.return_value = info['uri']

        return resource

    def setUp(self):
        self.user = MagicMock()
        self.org = MagicMock()
        self.user.userprofile.current_organization = self.org

        asset_manager.Resource = MagicMock()

        asset_manager.Resource.objects.filter.return_value = [self._mock_resource(r, self.org) for r in EXISTING_INFO]
        asset_manager.Resource.objects.get.return_value = self._mock_resource(EXISTING_INFO[0], self.org)


    @classmethod
    def tearDownClass(cls):
        # Restore resource model
        reload(asset_manager)
        super(ResourceRetrievingTestCase, cls).tearDownClass()

    def validate_response(self, result, expected_result, error, err_type, err_msg):
        if err_type is None:
            # Assert that no error occurs
            self.assertEquals(error, None)
            # Check result
            self.assertEquals(result, expected_result)
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)

    @parameterized.expand([
        ([RESOURCE_DATA1, RESOURCE_DATA2, RESOURCE_DATA3, RESOURCE_DATA4],),
        ([RESOURCE_DATA1], {"offset": 0, "size": 1}),
        ([RESOURCE_DATA2, RESOURCE_DATA3], {"offset": 1, "size": 2}),
        ([], {"offset": 5}, ValueError, "Missing required parameter in pagination"),
        ([], {"size": 8}, ValueError, "Missing required parameter in pagination"),
        ([], {"offset": -1, "size": 8}, ValueError, "Invalid pagination limits"),
        ([], {"offset": 1, "size": 0}, ValueError, "Invalid pagination limits"),
        ([], {"offset": 5, "size": -1}, ValueError, "Invalid pagination limits"),
        ([], {"offset": -6, "size": 2}, ValueError, "Invalid pagination limits"),
        ([], {"offset": -1, "size": 0}, ValueError, "Invalid pagination limits")
    ])
    def test_resource_retrieving(self, expected_result, pagination=None, err_type=None, err_msg=None):

        # Call the method
        error = None
        result = None
        try:
            am = asset_manager.AssetManager()
            result = am.get_provider_assets_info(self.user, pagination)
        except Exception as e:
            error = e

        self.validate_response(result, expected_result, error, err_type, err_msg)

    def _not_found(self):
        asset_manager.Resource.objects.get.side_effect = Exception('Not found')

    @parameterized.expand([
        ('basic', RESOURCE_DATA1, ),
        ('not_found', [], _not_found, ObjectDoesNotExist, 'The specified digital asset does not exists')
    ])
    def test_single_asset_retrieving(self, name, expected_result, side_effect=None, err_type=None, err_msg=None):

        if side_effect is not None:
            side_effect(self)

        error = None
        result = None
        try:
            am = asset_manager.AssetManager()
            result = am.get_asset_info('111')
        except Exception as e:
            error = e

        self.validate_response(result, expected_result, error, err_type, err_msg)

    @parameterized.expand([
        ('basic', [RESOURCE_DATA1, RESOURCE_DATA2, RESOURCE_DATA3, RESOURCE_DATA4])
    ])
    def test_assets_from_product(self, name, expected_result, side_effect=None, err_type=None, err_msg=None):
        if side_effect is not None:
            side_effect(self)

        error = None
        result = None
        try:
            am = asset_manager.AssetManager()
            result = am.get_product_assets('123')
        except Exception as e:
            error = e

        asset_manager.Resource.objects.filter.assert_called_once_with(product_id='123')
        self.validate_response(result, expected_result, error, err_type, err_msg)


class UploadAssetTestCase(TestCase):

    tags = ('asset-manager', )
    _file = None

    def setUp(self):
        import wstore.store_commons.rollback
        wstore.store_commons.rollback.rollback = decorator_mock

        self._user = MagicMock()
        self._user.userprofile.current_organization.name = 'test_user'

        asset_manager.Context = MagicMock()
        self._context_mock = MagicMock()
        self._context_mock.site.domain = 'http://testdomain.com/'
        asset_manager.Context.objects.all.return_value = [self._context_mock]

        asset_manager.Resource = MagicMock()
        self.res_mock = MagicMock()
        self.res_mock.get_url.return_value = "http://locationurl.com/"
        self.res_mock.get_uri.return_value = "http://uri.com/"
        asset_manager.Resource.objects.create.return_value = self.res_mock
        asset_manager.Resource.objects.get.return_value = self.res_mock

        asset_manager.os.path.isdir = MagicMock()
        asset_manager.os.path.exists = MagicMock()
        asset_manager.os.path.exists.return_value = False

        self.open_mock = mock_open()
        self._old_open = asset_manager.__builtins__['open']
        asset_manager.__builtins__['open'] = self.open_mock

    def tearDown(self):
        import wstore.store_commons.rollback
        reload(wstore.store_commons.rollback)

        self._file = None
        asset_manager.__builtins__['open'] = self._old_open
        reload(asset_manager)

    def _use_file(self):
        # Mock file
        self._file = MagicMock(name="example.wgt")
        self._file.name = "example.wgt"
        self._file.read.return_value = "Test data content"
        asset_manager.os.path.isdir.return_value = False
        asset_manager.os.mkdir = MagicMock()

    def _file_conflict(self):
        asset_manager.os.path.exists.return_value = True
        self.res_mock.product_id = None

    def _file_conflict_err(self):
        asset_manager.os.path.exists.return_value = True
        self.res_mock.product_id = '1'

    @parameterized.expand([
        ('basic', UPLOAD_CONTENT),
        ('file', {'contentType': 'application/x-widget'}, _use_file),
        ('existing_override', UPLOAD_CONTENT, _file_conflict, True),
        ('inv_file_name', MISSING_TYPE, None, False, ValueError, 'Missing required field: contentType'),
        ('inv_file_name', UPLOAD_INV_FILENAME, None, False, ValueError, 'Invalid file name format: Unsupported character'),
        ('existing', UPLOAD_CONTENT, _file_conflict_err, True, ConflictError, 'The provided digital asset (example.wgt) already exists'),
        ('not_provided', {'contentType': 'application/x-widget'}, None, False, ValueError, 'The digital asset has not been provided'),
        ('inv_content_field', {
            'contentType': 'application/x-widget',
            'content': ['http://content.com']
        }, None, False, TypeError, 'content field has an unsupported type, expected string or object')
    ])
    @override_settings(MEDIA_ROOT='/home/test/media')
    def test_upload_asset(self, name, data, side_effect=None, override=False, err_type=None, err_msg=None):

        if side_effect is not None:
            side_effect(self)

        am = asset_manager.AssetManager()
        am.rollback_logger = {
            'files': [],
            'models': []
        }

        error = None
        try:
            resource = am.upload_asset(self._user, data, file_=self._file)
        except Exception as e:
            error = e

        if err_type is None:
            # Check not error
            self.assertTrue(error is None)

            # Check calls
            self.assertEquals(self.res_mock, resource)
            self.assertEquals("http://locationurl.com/", resource.get_url())
            self.assertEqual("http://uri.com/", resource.get_uri())
            asset_manager.os.path.isdir.assert_called_once_with("/home/test/media/assets/test_user")
            asset_manager.os.path.exists.assert_called_once_with("/home/test/media/assets/test_user/example.wgt")
            self.open_mock.assert_called_once_with("/home/test/media/assets/test_user/example.wgt", "wb")
            self.open_mock().write.assert_called_once_with("Test data content")

            # Check rollback logger
            self.assertEquals({
                'files': ["/home/test/media/assets/test_user/example.wgt"],
                'models': [self.res_mock]
            }, am.rollback_logger)

            # Check file calls
            if self._file is not None:
                self._file.seek.assert_called_once_with(0)
                asset_manager.os.mkdir.assert_called_once_with("/home/test/media/assets/test_user")

            # Check override calls
            if override:
                asset_manager.Resource.objects.get.assert_called_once_with(resource_path='media/assets/test_user/example.wgt')
                self.res_mock.delete.assert_called_once_with()

            # Check resource creation
            asset_manager.Resource.objects.create.assert_called_once_with(
                provider=self._user.userprofile.current_organization,
                version='',
                download_link='http://testdomain.com/charging/media/assets/test_user/example.wgt',
                resource_path='media/assets/test_user/example.wgt',
                content_type='application/x-widget',
                resource_type='',
                state='',
                is_public=False,
                meta_info={}
            )
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(err_msg, unicode(error))

    def _mock_resource_type(self, form):
        asset_manager.ResourcePlugin = MagicMock()
        asset_manager.Resource.objects.filter.return_value = []
        asset_manager.ResourcePlugin.objects.filter.return_value = [MagicMock(
            media_types=[],
            name='service',
            formats=['URL'],
            form=form
        )]

    BASIC_META = {
        'field1': 'value',
        'field2': True,
        'field3': 'value2'
    }

    BASIC_FORM = {
        'field1': {
            'type': 'text'
        },
        'field2': {
            'type': 'checkbox'
        },
        'field3': {
            'type': 'select',
            'options': [{
                'value': 'value2'
            }]
        }
    }
    LINK = 'http://myservices.com'
    LINK_CONTENT = {
        'contentType': 'application/json',
        'resourceType': 'service',
        'content': LINK
    }

    @parameterized.expand([
        ('no_metainfo', None, {}, {}),
        ('metainfo', BASIC_META, BASIC_META, BASIC_FORM),
        ('default_metainfo', {
            'field1': 'value1'
        }, {
            'field1': 'value1',
            'field2': 'value2'
        }, {
            'field1': {
                'type': 'text'
            },
            'field2': {
                'type': 'text',
                'default': 'value2'
            },
        })
    ])
    def test_upload_asset_url_type(self, name, meta, exp_meta, form):
        content = deepcopy(self.LINK_CONTENT)

        if meta is not None:
            content['metadata'] = meta

        self._mock_resource_type(form)

        am = asset_manager.AssetManager()
        am.rollback_logger = {
            'files': [],
            'models': []
        }

        am.upload_asset(self._user, content)

        self.assertEquals({
            'files': [],
            'models': [self.res_mock]
        }, am.rollback_logger)

        # Check calls
        asset_manager.Resource.objects.filter.assert_called_once_with(download_link=self.LINK, provider=self._user.userprofile.current_organization)
        asset_manager.ResourcePlugin.objects.filter.assert_called_once_with(name='service')

        # Check resource creation
        asset_manager.Resource.objects.create.assert_called_once_with(
            provider=self._user.userprofile.current_organization,
            version='',
            download_link=self.LINK,
            resource_path='',
            content_type='application/json',
            resource_type='service',
            state='',
            is_public=False,
            meta_info=exp_meta
        )

    def test_upload_asset_pending(self):
        content = deepcopy(self.LINK_CONTENT)
        content['metadata'] = self.BASIC_META

        self._mock_resource_type(self.BASIC_FORM)

        am = asset_manager.AssetManager()
        am.rollback_logger = {
            'files': [],
            'models': []
        }

        assets = [MagicMock(product_id=None), MagicMock(product_id=None)]
        asset_manager.Resource.objects.filter.return_value = assets
        am.upload_asset(self._user, content)

        # Check calls
        asset_manager.Resource.objects.filter.assert_called_once_with(
            download_link=self.LINK, provider=self._user.userprofile.current_organization)

        assets[0].delete.assert_called_once_with()
        assets[1].delete.assert_called_once_with()

    def _existing_asset(self):
        asset_manager.Resource.objects.filter.return_value = [MagicMock(product_id='1')]

    def _type_not_found(self):
        asset_manager.ResourcePlugin.objects.filter.return_value = []

    def _inv_content(self):
        asset_manager.ResourcePlugin.objects.filter.return_value = [MagicMock(
            media_types=['text'],
            name='service',
            formats=['URL'],
        )]

    def _inv_format(self):
        asset_manager.ResourcePlugin.objects.filter.return_value = [MagicMock(
            media_types=[],
            name='service',
            formats=['FILE'],
        )]

    @parameterized.expand([
        ('conflict', deepcopy(LINK_CONTENT), _existing_asset, None, {}, ConflictError, 'The provided digital asset already exists'),
        ('invalid_url', {
            'contentType': 'application/json',
            'resourceType': 'service',
            'content': 'invalid url'
        }, None, None, {}, ValueError, 'The provided content is not a valid URL'),
        ('no_type_metadata', {
            'contentType': 'application/json',
            'content': LINK
        }, None, BASIC_META, {}, ValueError, 'You have to specify a valid asset type for providing meta data'),
        ('type_not_found', deepcopy(LINK_CONTENT), _type_not_found, None, {}, ObjectDoesNotExist, 'The asset type service does not exists'),
        ('inv_content', deepcopy(LINK_CONTENT), _inv_content, None, {}, ValueError, 'The content type application/json is not valid for the specified asset type'),
        ('inv_format', deepcopy(LINK_CONTENT), _inv_format, None, {},  ValueError, 'The format used for providing the digital asset (URL) is not valid for the given asset type'),
        ('meta_not_allowed', deepcopy(LINK_CONTENT), None, BASIC_META, {}, ValueError, 'The specified asset type does not allow meta data'),
        ('missing_mandatory_meta', deepcopy(LINK_CONTENT), None, BASIC_META, {
            'field1': {
                'type': 'text'
            },
            'field2': {
                'type': 'checkbox'
            },
            'field3': {
                'type': 'text',
            },
            'field4': {
                'type': 'text',
                'mandatory': True
            }
        }, ValueError, 'Missing mandatory field field4 in metadata'),
        ('inv_meta_text_type', deepcopy(LINK_CONTENT), None, {
            'field1': True,
            'field2': True,
            'field3': 'value2'
        }, BASIC_FORM, TypeError, 'Metadata field field1 must be a string'),
        ('inv_meta_bool_type', deepcopy(LINK_CONTENT), None, {
            'field1': 'value',
            'field2': 'true',
            'field3': 'value2'
        }, BASIC_FORM, TypeError, 'Metadata field field2 must be a boolean'),
        ('unkown_option', deepcopy(LINK_CONTENT), None, {
            'field1': 'value',
            'field2': True,
            'field3': 'value5'
        }, BASIC_FORM, ValueError, 'Metadata field field3 value is not one of the available options')
    ])
    def test_upload_asset_url_type_error(self, name, content, side_effect, meta, form, err_type, err_msg):

        if meta is not None:
            content['metadata'] = meta

        self._mock_resource_type(form)

        if side_effect is not None:
            side_effect(self)

        am = asset_manager.AssetManager()

        error = None
        try:
            am.upload_asset(self._user, content)
        except Exception as e:
            error = e

        self.assertTrue(isinstance(error, err_type))
        self.assertEquals(err_msg, unicode(error))


class ResourceModelTestCase(TestCase):
    tags = ('resource-model', )

    def test_resource_model(self):
        models.Context = MagicMock()
        ctx = MagicMock()
        ctx.site.domain = 'http://testserver.com/'

        models.Context.objects.all.return_value = [ctx]

        url = 'http://example.com/media/resource'

        from wstore.models import Organization
        org = Organization.objects.create(name='Test')

        res = models.Resource.objects.create(
            provider=org,
            version='1.0',
            download_link=url,
            resource_path='',
            content_type='',
            resource_type='',
            state=''
        )

        uri = 'http://testserver.com/charging/api/assetManagement/assets/' + res.pk
        self.assertEquals(url, res.get_url())
        self.assertEquals(uri, res.get_uri())