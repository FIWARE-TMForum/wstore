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

import json
from datetime import datetime
from mock import MagicMock, call
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.ordering import views
from wstore.ordering.errors import OrderingError


def api_call(self, collection, data, side_effect):
    # Create request
    self.request = MagicMock()
    self.request.META.get.return_value = 'application/json'
    self.request.user.is_anonymous.return_value = False
    self.request.user.userprofile.current_organization.tax_address = {
        'street': 'fake'
    }

    if isinstance(data, dict):
        data = json.dumps(data)

    self.request.body = data

    if side_effect is not None:
        side_effect(self)

    # Call api
    response = collection.create(self.request)

    # Parse result
    return response, json.loads(response.content)


CORRECT_RESP = {
    'result': 'correct',
    'message': 'OK'
}


class OrderingCollectionTestCase(TestCase):

    tags = ('ordering', 'ordering-view')

    def _missing_billing(self):
        self.request.user.userprofile.current_organization.tax_address = {}

    def _ordering_error(self):
        views.OrderingManager().process_order.side_effect = OrderingError('order error')

    def _exception(self):
        views.OrderingManager().process_order.side_effect = Exception('Unexpected error')

    @parameterized.expand([
        ('basic', {
            'id': 1,
            'orderItem': [{
                'id': '2'
            }, {
                'id': '3'
            }]
        }, None, 200, CORRECT_RESP),
        ('redirection', {
            'id': 1
        }, 'http://redirection.com/', 200, {
            'redirectUrl': 'http://redirection.com/'
        }),
        ('invalid_data', 'invalid', None, 400, {
            'result': 'error',
            'error': 'The provided data is not a valid JSON object'
        }, False),
        ('ordering_error', {}, None, 400, {
            'result': 'error',
            'error': 'order error'
        }, True, True, _ordering_error),
        ('exception', {}, None, 500, {
            'result': 'error',
            'error': 'Your order could not be processed'
        }, True, True, _exception)
    ])
    def test_create_order(self, name, data, redirect_url, exp_code, exp_response, called=True, failed=False, side_effect=None):
        # Create mocks
        views.OrderingManager = MagicMock()
        views.OrderingManager().process_order.return_value = redirect_url

        views.OrderingClient = MagicMock()
        views.Order = MagicMock()
        order = MagicMock()
        views.Order.objects.get.return_value = order

        c1 = MagicMock()
        c2 = MagicMock()
        c1.offering.is_digital = True
        c2.offering.is_digital = False
        order.get_item_contract.side_effect = [c1, c2]

        collection = views.OrderingCollection(permitted_methods=('POST',))
        response, body = api_call(self, collection, data, side_effect)

        self.assertEquals(exp_code, response.status_code)
        self.assertEquals(exp_response, body)

        if called:
            views.OrderingManager().process_order.assert_called_once_with(self.request.user, data)

            if redirect_url is None and not failed:
                self.assertEquals([
                    call(data, 'InProgress'),
                ], views.OrderingClient().update_state.call_args_list)

                self.assertEquals([
                    call(data, 'Completed', [{'id': '2'}])
                ], views.OrderingClient().update_items_state.call_args_list)

        if failed:
            self.assertEquals([call(data, 'InProgress')], views.OrderingClient().update_state.call_args_list)
            self.assertEquals([call(data, 'Failed')], views.OrderingClient().update_items_state.call_args_list)


BASIC_PRODUCT_EVENT = {
    'eventType': 'ProductCreationNotification',
    'event': {
        'product': {
            'id': 1,
            'name': 'oid=23',
            'productOffering': {
                'id': 10
            }
        }
    }
}


class InventoryCollectionTestCase(TestCase):

    tags = ('inventory', 'inventory-view')

    _ren_date = datetime(2016, 06, 01)

    def _initial_charge(self):
        self.contract.charges = [MagicMock()]
        self.contract.pricing_model = {
            'single_payment': []
        }

    def _subscription_charge(self):
        self.contract.charges = [MagicMock()]
        self.contract.pricing_model = {
            'subscription': [{
                'renovation_date': self._ren_date
            }]
        }

    def _missing_contract(self):
        self.contract.offering.off_id = 26

    def _activation_error(self):
        views.on_product_acquired.side_effect = Exception('Error')

    @parameterized.expand([
        ('basic', BASIC_PRODUCT_EVENT, 200, CORRECT_RESP),
        ('initial_charge', BASIC_PRODUCT_EVENT, 200, CORRECT_RESP, True, _initial_charge, True),
        ('subscription_charge', BASIC_PRODUCT_EVENT, 200, CORRECT_RESP, True, _subscription_charge, True, _ren_date),
        ('no_creation', {
            'eventType': 'ProductUpdateNotification'
        }, 200, CORRECT_RESP, False),
        ('invalid_data', 'invalid', 400, {
            'result': 'error',
            'error': 'The provided data is not a valid JSON object'
        }, False),
        ('missing_contract', BASIC_PRODUCT_EVENT, 404, {
            'result': 'error',
            'error': 'There is not a contract for the specified product'
        }, False, _missing_contract),
        ('activation_failure', BASIC_PRODUCT_EVENT, 400, {
            'result': 'error',
            'error': 'The asset has failed to be activated'
        }, False, _activation_error)
    ])
    def test_activate_product(self, name, data, exp_code, exp_response, called=True, side_effect=None, billing_exp=False, exp_date=None):
        views.InventoryClient = MagicMock()
        views.on_product_acquired = MagicMock()

        views.BillingClient = MagicMock()

        self.contract = MagicMock()
        self.contract.offering.off_id = 10

        order = MagicMock()
        order.contracts = [MagicMock(), self.contract]

        views.Order = MagicMock()
        views.Order.objects.get.return_value = order

        collection = views.InventoryCollection(permitted_methods=('POST',))
        response, body = api_call(self, collection, data, side_effect)

        self.assertEquals(exp_code, response.status_code)
        self.assertEquals(exp_response, body)

        if called:
            views.Order.objects.get.assert_called_once_with(order_id='23')
            views.on_product_acquired.assert_called_once_with(order, self.contract)
            views.InventoryClient.assert_called_once_with()
            views.InventoryClient().activate_product.assert_called_once_with(1)
            self.assertEquals(1, self.contract.product_id)

        if billing_exp:
            views.BillingClient.assert_called_once_with()
            views.BillingClient().create_charge.assert_called_once_with(
                self.contract.charges[0], data['event']['product']['id'], start_date=None, end_date=exp_date)
        else:
            self.assertEquals(0, views.BillingClient.call_count)

RENOVATION_DATA = {
    'name': 'oid=1',
    'id': '24',
    'priceType': 'recurring'
}

MISSING_FIELD_RESP = {
    'result': 'error',
    'error': 'Missing required field, must contain name, id  and priceType fields'
}

INV_OID_RESP = {
    'result': 'error',
    'error': 'The oid specified in the product name is not valid'
}


class RenovationCollectionTestCase(TestCase):

    tags = ('renovation', )

    def _order_not_found(self):
        views.Order.objects.get.side_effect = Exception('Not found')

    def _product_not_found(self):
        views.Order.objects.get().get_product_contract.side_effect = OrderingError('Not found')

    def _charging_engine_value_error(self):
        self.charging_inst.resolve_charging.side_effect = ValueError('Value error')

    def _charging_engine_ordering_error(self):
        self.charging_inst.resolve_charging.side_effect = OrderingError('ordering error')

    def _charging_engine_exception(self):
        self.charging_inst.resolve_charging.side_effect = Exception('Exception')

    @parameterized.expand([
        ('subscription', RENOVATION_DATA, 'http://redirecturl.com', 'recurring', 200, CORRECT_RESP),
        ('usage', {
            'name': 'oid=1',
            'id': '24',
            'priceType': 'usage'
        }, 'http://redirecturl.com', 'usage', 200, CORRECT_RESP),
        ('free', {
            'name': 'oid=1',
            'id': '24',
            'priceType': 'recurring'
        }, None, 'recurring', 200, CORRECT_RESP),
        ('invalid_data', 'invalid_data', None, None, 400, {
            'result': 'error',
            'error': 'The provided data is not a valid JSON object'
        }),
        ('missing_name', {
            'id': '24',
            'priceType': 'recurring'
        }, None, None, 400, MISSING_FIELD_RESP),
        ('missing_id', {
            'name': 'oid=1',
            'priceType': 'recurring'
        }, None, None, 400, MISSING_FIELD_RESP),
        ('missing_price_type', {
            'name': 'oid=1',
            'id': '24'
        }, None, None, 400, MISSING_FIELD_RESP),
        ('invalid_oid', {
            'name': '1',
            'id': '24',
            'priceType': 'usage'
        }, None, None, 404, INV_OID_RESP),
        ('order_not_found', RENOVATION_DATA, None, None, 404, INV_OID_RESP, _order_not_found),
        ('invalid_product_id', RENOVATION_DATA, None, None, 404, {
            'result': 'error',
            'error': 'The specified product id is not valid'
        }, _product_not_found),
        ('invalid_type', {
            'name': 'oid=1',
            'id': '24',
            'priceType': 'one time'
        }, None, None, 400, {
            'result': 'error',
            'error': 'Invalid priceType only recurring and usage types can be renovated'
        }),
        ('charging_error_value', RENOVATION_DATA, None, None, 400, {
            'result': 'error',
            'error': 'Value error'
        }, _charging_engine_value_error),
        ('charging_error_ordering', RENOVATION_DATA, None, None, 422, {
            'result': 'error',
            'error': 'OrderingError: ordering error'
        }, _charging_engine_ordering_error),
        ('charging_error_unexp', RENOVATION_DATA, None, None, 500, {
            'result': 'error',
            'error': 'An unexpected event prevented your payment to be created'
        }, _charging_engine_exception)
    ])
    def test_renovate_product(self, name, data, url, concept, exp_code, exp_response, side_effect=None):
        # Create mocks
        views.Order = MagicMock()
        views.ChargingEngine = MagicMock()
        self.charging_inst = MagicMock()
        self.charging_inst.resolve_charging.return_value = url
        views.ChargingEngine.return_value = self.charging_inst

        views.on_usage_refreshed = MagicMock()

        collection = views.RenovationCollection(permitted_methods=('POST', ))
        response, body = api_call(self, collection, data, side_effect)

        self.assertEquals(exp_code, response.status_code)
        self.assertEquals(exp_response, body)

        if url is not None:
            self.assertEquals(url, response['X-Redirect-URL'])
        else:
            self.assertFalse('X-Redirect-URL' in response)

        # Validate calls if needed
        if concept is not None:
            views.Order.objects.get.assert_called_once_with(order_id='1')
            views.Order.objects.get().get_product_contract.assert_called_once_with('24')
            views.ChargingEngine.assert_called_once_with(views.Order.objects.get())
            self.charging_inst.resolve_charging.assert_called_once_with(
                type_=concept, related_contracts=[views.Order.objects.get().get_product_contract()])

            views.on_usage_refreshed.assert_called_once_with(
                views.Order.objects.get(), views.Order.objects.get().get_product_contract())