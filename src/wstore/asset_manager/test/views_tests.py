# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid

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

import json

from mock import MagicMock
from StringIO import StringIO
from nose_parameterized import parameterized

from django.test import TestCase
from django.test.client import RequestFactory, MULTIPART_CONTENT
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from wstore.asset_manager import views
from wstore.asset_manager.errors import ProductError
from wstore.models import UserProfile
from wstore.store_commons.errors import ConflictError

RESOURCE_DATA = {
    'contentType': 'application/zip',
    'content': {
        'name': 'testfile.zip',
        'content': 'content'
    }
}

BASIC_PRODUCT = {
    'action': 'create',
    'product': {}
}

MISSING_ACTION = {
    'product': {}
}

MISSING_PRODUCT = {
    'action': 'create'
}


class AssetCollectionTestCase(TestCase):

    tags = ('asset-api',)

    def setUp(self):
        # Create request factory
        self.factory = RequestFactory()
        # Create testing user
        self.user = User.objects.create_user(username='test_user', email='', password='passwd')
        self.user.is_anonymous = MagicMock(return_value=False)
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['provider', 'customer']
        self.user.userprofile.save()
        self.user.is_staff = False
        views.AssetManager = MagicMock()
        self.am_instance = MagicMock()
        views.AssetManager.return_value = self.am_instance
        views.User = MagicMock()
        views.User.objects.get.return_value = MagicMock()
        views.UserProfile = MagicMock()
        views.UserProfile.objets.get.return_value = MagicMock()
        views.UserProfile.objets.get().current_organization = 'organization'

    @classmethod
    def tearDownClass(cls):
        reload(views)
        super(AssetCollectionTestCase, cls).tearDownClass()

    def _no_provider(self):
        self.user.userprofile.get_current_roles = MagicMock(name='get_current_roles')
        self.user.userprofile.get_current_roles.return_value = ['customer']
        self.user.userprofile.save()

    def _anonymous(self):
        self.user.is_anonymous.return_value = True

    def _call_exception(self):
        self.am_instance.get_provider_assets_info.side_effect = Exception('Getting resources error')

    @parameterized.expand([
        ([{
            'name': 'test_resource',
            'provider': 'test_user',
            'version': '1.0'
        }],),
        ([{
            'name': 'test_resource',
            'provider': 'test_user',
            'version': '1.0'
        }], None, 200, None, None, "user"),
        ([{
            'name': 'test_resource',
            'provider': 'test_user',
            'version': '1.0'
        }], None, 200, None, {
            'offset': '1',
            'size': '1'
        }),
        ([], _anonymous, 401, 'Authentication required'),
        ([], _call_exception, 400, 'Getting resources error')
    ])
    def test_get_assets(self, return_value, side_effect=None, code=200, error_msg=None, pagination=None, user=None):

        # Mock get asset_manager method
        resource_collection = views.AssetCollection(permitted_methods=('GET',))

        self.am_instance.get_provider_assets_info.return_value = return_value

        path = '/api/offering/resources'

        if pagination is not None:
            path += '?offset=' + pagination['offset'] + '&size=' + pagination['size']

        if user is not None:
            path += "{}user={}".format("&" if "?" in path else "?", user)

        request = self.factory.get(path, HTTP_ACCEPT='application/json')

        request.user = self.user

        # Create the side effect if needed
        if side_effect:
            side_effect(self)

        views.User.reset_mock()
        views.UserProfile.reset_mock()

        # Call the view
        response = resource_collection.read(request)

        self.assertEquals(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        if not error_msg:
            views.AssetManager.assert_called_once_with()
            if user is not None:
                views.User.objects.get.assert_called_with(username=user)
                views.UserProfile.objects.get.assert_called_with(user=views.User.objects.get())
            user_called = self.user.userprofile if user is None else views.UserProfile.objects.get()
            self.am_instance.get_provider_assets_info.assert_called_once_with(user_called, pagination=pagination)
            self.assertEquals(type(body_response), list)
            self.assertEquals(body_response, return_value)
        else:
            self.assertEqual(type(body_response), dict)
            self.assertEqual(body_response['error'], error_msg)
            self.assertEqual(body_response['result'], 'error')

    def _not_found_asset(self):
        self.am_instance.get_asset_info.side_effect = ObjectDoesNotExist('Not found')

    def _call_exception_single(self):
        self.am_instance.get_asset_info.side_effect = Exception('Getting resources error')

    @parameterized.expand([
        ('basic', {
            'id': '1111'
        }, 200),
        ('not_found', {
            'error': 'Not found',
            'result': 'error'
        }, 404, _not_found_asset),
        ('exception', {
            'error': 'An unexpected error occurred',
            'result': 'error'
        }, 500, _call_exception_single)
    ])
    def test_get_asset(self, name, exp_value, exp_code, side_effect=None, called=True):
        resource_entry = views.AssetEntry(permitted_methods=('GET',))
        self.am_instance.get_asset_info.return_value = exp_value

        if side_effect is not None:
            side_effect(self)

        request = self.factory.get('/charging/api/assetsManagement/assets/1111', HTTP_ACCEPT='application/json')
        request.user = self.user

        response = resource_entry.read(request, '1111')
        self.assertEquals(response.status_code, exp_code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')

        body_response = json.loads(response.content)
        self.assertEquals(body_response, exp_value)

        if called:
            self.am_instance.get_asset_info.assert_called_once_with('1111')
        else:
            self.assertEquals(self.am_instance.get_asset_info.call_count, 0)

    def _creation_exception(self):
        self.am_instance.upload_asset.side_effect = Exception('Resource creation exception')

    def _existing(self):
        self.am_instance.upload_asset.side_effect = ConflictError('Resource exists')

    def _test_post_api(self, collection, content, content_type, side_effect=None, code=201, validator=None):

        resource_collection = collection(permitted_methods=('POST', ))

        # Build the request
        request = self.factory.post(
            '/api/offering/resources',
            content,
            content_type=content_type,
            HTTP_ACCEPT='application/json'
        )
        request.user = self.user

        # Create the side effect if needed
        if side_effect:
            side_effect(self)

        # Call the view
        response = resource_collection.create(request)

        self.assertEqual(response.status_code, code)
        self.assertEqual(response.get('Content-type'), 'application/json; charset=utf-8')
        body_response = json.loads(response.content)

        self.assertEqual(type(body_response), dict)
        validator(request, body_response)

    @parameterized.expand([
        (RESOURCE_DATA,),
        (RESOURCE_DATA, True),
        (RESOURCE_DATA, False, _no_provider, True, 403, "You don't have the seller role"),
        (RESOURCE_DATA, False, _creation_exception, True, 400, 'Resource creation exception'),
        (RESOURCE_DATA, True, _creation_exception, True, 400, 'Resource creation exception'),
        (RESOURCE_DATA, True, _creation_exception, True, 400, 'Resource creation exception'),
        (RESOURCE_DATA, True, _existing, True, 409, 'Resource exists')
    ])
    def test_upload_asset(self, data, file_=False, side_effect=None, error=False, code=200, msg='Created'):

        content_type = 'application/json'

        if file_:
            f = StringIO()
            f.name = 'test_file.txt'
            f.write('test file')
            content = {
                'json': json.dumps(data),
                'file': f
            }
            content_type = MULTIPART_CONTENT
        else:
            content = json.dumps(data)

        self.am_instance.upload_asset.return_value = 'http://locationurl.com/'

        def validator(request, body_response):
            if not error:
                # Check correct call
                if not file_:
                    self.am_instance.upload_asset.assert_called_once_with(self.user, data)
                else:
                    expected_file = request.FILES['file']
                    self.am_instance.upload_asset.assert_called_once_with(self.user, data, file_=expected_file)
                self.assertEquals(body_response, {
                    'contentType': 'application/zip',
                    'content': 'http://locationurl.com/'
                })
            else:
                self.assertEqual(body_response, {
                    'error': msg,
                    'result': 'error'
                })

        self._test_post_api(views.UploadCollection, content, content_type, side_effect, code, validator)

    def _prod_val_value_error(self):
        self.validator_instance.validate.side_effect = ValueError('Invalid value in product')

    def _prod_val_product_error(self):
        self.validator_instance.validate.side_effect = ProductError('Missing product information')

    def _prod_val_permission_denied(self):
        self.validator_instance.validate.side_effect = PermissionDenied('Permission denied')

    def _prod_val_exception(self):
        self.validator_instance.validate.side_effect = Exception('Unexpected error')

    @parameterized.expand([
        ('basic', BASIC_PRODUCT),
        ('not_provider', BASIC_PRODUCT, _no_provider, True, 403, "You don't have the seller role"),
        ('invalid_content', 'inv', None, True, 400, 'The content is not a valid JSON document'),
        ('missing_action', MISSING_ACTION, None, True, 400, 'Missing required field: action'),
        ('missing_product', MISSING_PRODUCT, None, True, 400, 'Missing required field: product'),
        ('value_error', BASIC_PRODUCT, _prod_val_value_error, True, 400, 'Invalid value in product'),
        ('product_error', BASIC_PRODUCT, _prod_val_product_error, True, 400, 'ProductError: Missing product information'),
        ('permission_denied', BASIC_PRODUCT, _prod_val_permission_denied, True, 403, 'Permission denied'),
        ('exception', BASIC_PRODUCT, _prod_val_exception, True, 500, 'An unexpected error has occurred')
    ])
    def test_validate_resource(self, name, data, side_effect=None, error=False, code=200, msg='OK'):
        views.ProductValidator = MagicMock()
        self.validator_instance = MagicMock()
        views.ProductValidator.return_value = self.validator_instance

        if isinstance(data, dict):
            content = json.dumps(data)
        else:
            content = data

        def validator(request, body_response):
            if not error:
                self.assertEqual(body_response['message'], msg)
                views.ProductValidator.assert_called_once_with()
                self.assertEqual(body_response['result'], 'correct')
                self.validator_instance.validate.assert_called_once_with(data['action'], self.user.userprofile.current_organization, data['product'])
            else:
                self.assertEqual(body_response['error'], msg)
                self.assertEqual(body_response['result'], 'error')

        self._test_post_api(views.ValidateCollection, content, 'application/json', side_effect, code, validator)

    def test_validate_offering(self):
        # Only the basic call is tested since the aux method used for processing the request has been already tested
        views.OfferingValidator = MagicMock()
        off_validator = MagicMock()
        views.OfferingValidator.return_value = off_validator

        data = json.dumps({
            'action': 'create',
            'offering': {}
        })

        def validator(request, body_response):
            views.OfferingValidator.assert_called_once_with()
            self.assertEquals(body_response, {
                'result': 'correct',
                'message': 'OK'
            })
            off_validator.validate.assert_called_once_with('create', self.user.userprofile.current_organization, {})

        self._test_post_api(views.ValidateOfferingCollection, data, 'application/json', None, 200, validator)
