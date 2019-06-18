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



import json
from mock import call

from store_commons.tests import *
from admin.users.tests import *

from django.test.client import RequestFactory

import views


class ServeMediaTestCase(TestCase):
    tags = ('media', )

    _resource_path = 'media/assets/test_user/widget.wgt'
    _expected_file = 'assets/test_user/widget.wgt'

    def setUp(self):
        # Mock user
        self._user = MagicMock()
        self._user.is_anonymous.return_value = False
        self._org = MagicMock()
        self._user.userprofile.current_organization = self._org

        views.Organization = MagicMock()
        views.Organization.objects.get.return_value = self._org

        # Mock Resource model
        views.Resource = MagicMock()
        self._asset_inst = MagicMock()
        self._asset_inst.is_public = False
        self._asset_inst.provider = self._org

        views.Resource.objects.filter.return_value = [self._asset_inst]

        # Mock serve and smart_str
        views.serve = MagicMock()
        views.smart_str = MagicMock()
        views.smart_str.return_value = 'smart string'

        # Mock is_file
        views.os.path.isfile = MagicMock()

        # Mock Order
        views.Order = MagicMock()
        order_inst = MagicMock()
        order_inst.owner_organization = self._org
        views.Order.objects.get.return_value = order_inst

        # Mock offering
        views.Offering = MagicMock()
        self._offering_inst = MagicMock()
        self._offering_inst.asset = self._asset_inst
        views.Offering.objects.get.side_effect = [MagicMock(), self._offering_inst]

    def _validate_res_call(self):
        views.Resource.objects.filter.assert_called_once_with(resource_path=self._resource_path)
        self.assertEqual(0, views.Order.objects.get.call_count)

    def _validate_off_call(self):
        self._validate_res_call()
        self.assertEqual([
            call(pk='offpk1'),
            call(pk='offpk2')
        ], views.Offering.objects.get.call_args_list)

    def _validate_bundle_call(self):
        self._validate_res_call()
        self.assertEqual([
            call(pk='offpk1'),
            call(pk='offpk2'),
            call(pk='offpk3'),
            call(pk='offpk3'),
            call(pk='offpk4'),
            call(pk='offpk4')
        ], views.Offering.objects.get.call_args_list)

    def _validate_product_bundle_call(self):
        views.Resource.objects.filter.assert_called_once_with(resource_path=self._resource_path)
        self.assertEqual([
            call(pk='prodpk1'),
            call(pk='prodpk2')
        ], views.Resource.objects.get.call_args_list)
        self.assertEqual(0, views.Order.objects.get.call_count)

        self.assertEqual([
            call(pk='offpk1'),
            call(pk='offpk2')
        ], views.Offering.objects.get.call_args_list)

    def _validate_upgrading_call(self):
        self.assertEqual([
            call(resource_path=self._resource_path),
            call(state='upgrading', provider=self._org)
        ], views.Resource.objects.filter.call_args_list)

        views.Organization.objects.get.assert_called_once_with(name='test_user')

    def _validate_order_call(self):
        views.Order.objects.get.assert_called_once_with(pk='111111111111111111111111')
        self.assertEqual(0, views.Resource.objects.get.call_count)

    def _validate_empty_call(self):
        self.assertEqual(0, views.Resource.objects.get.call_count)
        self.assertEqual(0, views.Order.objects.get.call_count)

    def _validate_error(self, response, expected):
        resp = json.loads(response.content)
        self.assertEqual(expected[0], response.status_code)
        self.assertEqual(expected[1], resp)

    def _validate_serve(self, response, expected):
        views.os.path.isfile(expected)
        views.serve.assert_called_once_with(self.request, expected, document_root='/home/test/media/')

    def _validate_xfile(self, response, expected):
        views.os.path.isfile(expected)
        views.smart_str.assert_called_once_with(expected)
        self.assertEqual('smart string', response['X-Sendfile'])

    def _public_asset(self):
        self._asset_inst.is_public = True
        self._asset_inst.provider = MagicMock()

    def _usexfiles(self):
        views.settings = MagicMock()
        views.settings.USE_XSENDFILE = True
        views.settings.MEDIA_ROOT = '/home/test/media/'
        views.settings.MEDIA_URL = '/media/'
        views.settings.MEDIA_DIR = 'media/'

    def _asset_error(self):
        views.Resource.objects.filter.return_value = []

    def _order_error(self):
        views.Order.objects.get.side_effect = Exception('Not found')

    def _unauthorized(self):
        self._acquired()
        views.Offering.objects.get.side_effect = [MagicMock(is_digital=False),
                                                  MagicMock(is_digital=True, asset=MagicMock())]

    def _not_loged(self):
        self._user.is_anonymous.return_value = True

    def _not_found(self):
        views.os.path.isfile.return_value = False

    def _acquired(self):
        self._user.userprofile.current_organization = MagicMock()
        self._user.userprofile.current_organization.acquired_offerings = ['offpk1', 'offpk2']

    def _bundle_acquired(self):
        self._acquired()
        self._offering_inst = MagicMock(asset=None, bundled_offerings=['offpk3', 'offpk4'])

        views.Offering.objects.get.side_effect = [MagicMock(), self._offering_inst,
                                                  MagicMock(is_digital=True, asset=MagicMock()),
                                                  MagicMock(is_digital=True, asset=MagicMock()),
                                                  MagicMock(is_digital=True, asset=self._asset_inst),
                                                  MagicMock(is_digital=True, asset=self._asset_inst)]

    def _product_bundle_acquired(self):
        self._acquired()
        self._offering_inst.asset = MagicMock(bundled_assets=['prodpk1', 'prodpk2'])

        views.Resource.objects.get.side_effect = [self._asset_inst, MagicMock(), self._asset_inst]

    def _upgrading(self):
        self._asset_inst.old_versions = [MagicMock(resource_path=self._resource_path)]
        views.Resource.objects.filter.side_effect = [[], [MagicMock(old_versions=[]), self._asset_inst]]

    @parameterized.expand([
        ('asset', 'assets/test_user', 'widget.wgt', _validate_res_call, _validate_serve, _expected_file),
        ('asset_acquired', 'assets/test_user', 'widget.wgt', _validate_off_call, _validate_serve, _expected_file, _acquired),
        ('asset_in_bundle', 'assets/test_user', 'widget.wgt', _validate_bundle_call, _validate_serve, _expected_file, _bundle_acquired),
        ('asset_in_product_bundle', 'assets/test_user', 'widget.wgt', _validate_product_bundle_call, _validate_serve, _expected_file, _product_bundle_acquired),
        ('public_asset', 'assets/test_user', 'widget.wgt', _validate_res_call, _validate_serve, _expected_file, _public_asset),
        ('upgrading_asset', 'assets/test_user', 'widget.wgt', _validate_upgrading_call, _validate_serve, _expected_file, _upgrading),
        ('invoice', 'bills', '111111111111111111111111_userbill.pdf', _validate_order_call, _validate_xfile, 'bills/111111111111111111111111_userbill.pdf', _usexfiles),
        ('asset_not_found', 'assets/test_user', 'widget.wgt', _validate_upgrading_call, _validate_error, (404, {
            'result': 'error',
            'error': 'The specified asset does not exists'
        }), _asset_error),
        ('asset_anonymous', 'assets/test_user', 'widget.wgt', _validate_res_call, _validate_error, (401, {
            'result': 'error',
            'error': 'You must be authenticated to download the specified asset'
        }), _not_loged),
        ('asset_unauthorized', 'assets/test_user', 'widget.wgt', _validate_res_call, _validate_error, (403, {
            'result': 'error',
            'error': 'You are not authorized to download the specified asset'
        }), _unauthorized),
        ('invoice_not_found', 'bills', '111111111111111111111111_userbill.pdf', _validate_order_call, _validate_error, (404, {
            'result': 'error',
            'error': 'The specified invoice does not exists'
        }), _order_error),
        ('invoice_anonymous', 'bills', '111111111111111111111111_userbill.pdf', _validate_empty_call, _validate_error, (401, {
            'result': 'error',
            'error': 'You must provide credentials for downloading invoices'
        }), _not_loged),
        ('invoice_unauthorized', 'bills', '111111111111111111111111_userbill.pdf', _validate_order_call, _validate_error, (403, {
            'result': 'error',
            'error': 'You are not authorized to download the specified invoice'
        }), _unauthorized),
        ('file_not_found', 'assets/test_user', 'widget.wgt', _validate_res_call, _validate_error, (404, {
            'result': 'error',
            'error': 'Resource not found'
        }), _not_found),
        ('invalid_type', 'invalid/user', 'widget.wgt', _validate_empty_call, _validate_error, (404, {
            'result': 'error',
            'error': 'Resource not found'
        }))
    ])
    @override_settings(MEDIA_ROOT='/home/test/media/', MEDIA_URL='/media/', MEDIA_DIR='media/')
    def test_serve_media(self, name, path, file_name, call_validator, res_validator, expected, side_effect=None):

        if side_effect is not None:
            side_effect(self)

        factory = RequestFactory()
        self.request = factory.post(
            'media/' + path + '/' + file_name,
            HTTP_ACCEPT='application/json'
        )
        self.request.user = self._user

        media_view = views.ServeMedia(permitted_methods=('GET',))

        response = media_view.read(self.request, path, file_name)
        call_validator(self)
        res_validator(self, response, expected)
