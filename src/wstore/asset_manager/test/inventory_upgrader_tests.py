# -*- coding: utf-8 -*-

# Copyright (c) 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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



from bson import ObjectId
from copy import deepcopy
from mock import MagicMock, call
from requests.exceptions import HTTPError

from django.test.testcases import TestCase

from wstore.asset_manager import inventory_upgrader


class InventoryUpgraderTestCase(TestCase):

    tags = ('upgrades', )

    _prev_asset_chars = [{
        'name': 'Media Type',
        'value': 'application/xml'
    }, {
        'name': 'Asset type',
        'value': 'Service'
    }, {
        'name': 'Location',
        'value': 'https://myservice.com/v1'
    }]

    _new_media_type = 'application/json'
    _new_location = 'https://myservice.com/v2'

    _product_off_id = '123'
    _product_off_id2 = '456'
    _product_off_id3 = '789'
    _off_bundle_id = '000'
    _off_bundle_id2 = '222'
    _product_off_pk = 'abc'
    _product_off_pk2 = 'ab1'
    _product_off_pk3 = 'ad7'
    _off_bundle_pk = '111'
    _off_bundle_pk2 = '333'

    _off_bundle_chars = [{
        'name': 'offering:{} Media Type'.format(_product_off_id),
        'value': 'application/xml'
    }, {
        'name': 'offering:asd Asset type',
        'value': 'Service'
    }, {
        'name': 'offering:{} Location'.format(_product_off_id),
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'offering:asd Media Type',
        'value': 'application/xml'
    }, {
        'name': 'offering:{} Asset type'.format(_product_off_id),
        'value': 'Service'
    }, {
        'name': 'offering:asd Location',
        'value': 'https://myservice.com/v1'
    }]

    _new_off_bundle_chars = [{
        'name': 'offering:asd Asset type',
        'value': 'Service'
    }, {
        'name': 'offering:asd Media Type',
        'value': 'application/xml'
    }, {
        'name': 'offering:asd Location',
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'offering:{} Media Type'.format(_product_off_id),
        'value': _new_media_type
    }, {
        'name': 'offering:{} Asset Type'.format(_product_off_id),
        'value': 'Service'
    }, {
        'name': 'offering:{} Location'.format(_product_off_id),
        'value': _new_location
    }]

    _product_spec_id = '10'
    _product_spec_id2 = '20'

    _product_bundle_chars = [{
        'name': 'product:{} Media Type'.format(_product_spec_id),
        'value': 'application/xml'
    }, {
        'name': 'product:{} Asset type'.format(_product_spec_id2),
        'value': 'Service'
    }, {
        'name': 'product:{} Location'.format(_product_spec_id),
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'product:{} Media Type'.format(_product_spec_id2),
        'value': 'application/xml'
    }, {
        'name': 'product:{} Asset type'.format(_product_spec_id),
        'value': 'Service'
    }, {
        'name': 'product:{} Location'.format(_product_spec_id2),
        'value': 'https://myservice.com/v1'
    }]

    _new_product_bundle_chars = [{
        'name': 'product:{} Asset type'.format(_product_spec_id2),
        'value': 'Service'
    }, {
        'name': 'product:{} Media Type'.format(_product_spec_id2),
        'value': 'application/xml'
    }, {
        'name': 'product:{} Location'.format(_product_spec_id2),
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'product:{} Media Type'.format(_product_spec_id),
        'value': _new_media_type
    }, {
        'name': 'product:{} Asset Type'.format(_product_spec_id),
        'value': 'Service'
    }, {
        'name': 'product:{} Location'.format(_product_spec_id),
        'value': _new_location
    }]

    _mixed_bundle_chars = [{
        'name': 'offering:{} product:{} Media Type'.format(_product_off_id3, _product_spec_id),
        'value': 'application/xml'
    }, {
        'name': 'offering:{} product:{} Asset type'.format(_product_off_id3, _product_spec_id),
        'value': 'Service'
    }, {
        'name': 'offering:{} product:{} Location'.format(_product_off_id3, _product_spec_id),
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'offering:asd Media Type',
        'value': 'application/xml'
    }, {
        'name': 'offering:asd Asset type',
        'value': 'Service'
    }, {
        'name': 'offering:asd Location',
        'value': 'https://myservice.com/v1'
    }]

    _new_mixed_bundle_chars = [{
        'name': 'offering:asd Media Type',
        'value': 'application/xml'
    }, {
        'name': 'offering:asd Asset type',
        'value': 'Service'
    }, {
        'name': 'offering:asd Location',
        'value': 'https://myservice.com/v1'
    }, {
        'name': 'offering:{} product:{} Media Type'.format(_product_off_id3, _product_spec_id),
        'value': _new_media_type
    }, {
        'name': 'offering:{} product:{} Asset Type'.format(_product_off_id3, _product_spec_id),
        'value': 'Service'
    }, {
        'name': 'offering:{} product:{} Location'.format(_product_off_id3, _product_spec_id),
        'value': _new_location
    }]

    _product1 = {
        'id': 1,
        'name': ' oid=11',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product1['productCharacteristic'].append({
        'name': 'speed',
        'value': '100mbps'
    })

    _product2 = {
        'id': 2,
        'name': ' oid=22',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product2['productCharacteristic'].append({
        'name': 'speed',
        'value': '20mbps'
    })

    _product3 = {
        'id': 3,
        'name': ' oid=33',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product4 = {
        'id': 4,
        'name': ' oid=44',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product5 = {
        'id': 5,
        'name': ' oid=55',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product6 = {
        'id': 6,
        'name': ' oid=66',
        'productCharacteristic': deepcopy(_prev_asset_chars)
    }

    _product_p_bundle = {
        'id': 7,
        'name': ' oid=77',
        'productCharacteristic': deepcopy(_product_bundle_chars)
    }

    _product_off_bundle = {
        'id': 8,
        'name': ' oid=88',
        'productCharacteristic': deepcopy(_off_bundle_chars)
    }

    _product_mix_bundle = {
        'id': 9,
        'name': ' oid=99',
        'productCharacteristic': deepcopy(_mixed_bundle_chars)
    }

    _ctx_pk = '58a447608e05ac5752d96d98'
    _asset_pk = '1111'
    _product_spec_name = 'product'
    _new_media_type = 'application/json'
    _new_location = 'https://myservice.com/v2'

    _new_asset_chars = [{
        'name': 'Media Type',
        'value': _new_media_type
    }, {
        'name': 'Asset Type',
        'value': 'Service'
    }, {
        'name': 'Location',
        'value': _new_location
    }]

    _catalog_url = 'http://localhost:8080/catalog'
    _product_spec_url = '{}/api/catalogManagement/v2/productSpecification/{}?fields=name'.format(_catalog_url, _product_spec_id)

    def setUp(self):
        # Mock Context
        self._ctx_instance = MagicMock(failed_upgrades=[])
        self._ctx_instance.pk = self._ctx_pk

        inventory_upgrader.Context = MagicMock()
        inventory_upgrader.Context.objects.all.return_value = [self._ctx_instance]

        inventory_upgrader.Offering = MagicMock()
        inventory_upgrader.Resource = MagicMock()
        inventory_upgrader.Resource.objects.filter.return_value = []

        # Mock Inventory client
        self._client_instance = MagicMock()
        inventory_upgrader.InventoryClient = MagicMock(return_value=self._client_instance)

        # Mock database connector
        self._lock_inst = MagicMock()
        inventory_upgrader.DocumentLock = MagicMock(return_value=self._lock_inst)

        inventory_upgrader.requests = MagicMock()
        self._resp = MagicMock()
        self._resp.json.return_value = {
            'name': self._product_spec_name
        }
        inventory_upgrader.requests.get.return_value = self._resp

        inventory_upgrader.PAGE_LEN = 2.0

        self._asset = MagicMock()
        self._asset.pk = self._asset_pk
        self._asset.product_id = self._product_spec_id
        self._asset.content_type = self._new_media_type
        self._asset.resource_type = 'Service'
        self._asset.download_link = self._new_location

        self._cat_url = inventory_upgrader.settings.CATALOG
        inventory_upgrader.settings.CATALOG = self._catalog_url

        # Mock Orders
        self._order_int = MagicMock()
        inventory_upgrader.Order = MagicMock()
        inventory_upgrader.Order.objects.get.return_value = self._order_int

        # Mock user notifier
        self._not_handler = MagicMock()
        inventory_upgrader.NotificationsHandler = MagicMock(return_value=self._not_handler)

    def tearDown(self):
        inventory_upgrader.settings.CATALOG = self._cat_url

    def _check_product_spec_retrieved(self):
        inventory_upgrader.requests.get.assert_called_once_with(self._product_spec_url)
        self._resp.raise_for_status.assert_called_once_with()
        self._resp.json.assert_called_once_with()

    def _check_single_get_call(self):
        self._client_instance.get_products.assert_called_once_with(query={
            'productOffering.id': self._product_off_id,
            'fields': 'id'
        })

        self.assertEqual(0, self._client_instance.patch_product.call_count)

    def test_inventory_upgrader_no_offerings(self):
        inventory_upgrader.Offering.objects.filter.return_value = []

        upgrader = inventory_upgrader.InventoryUpgrader(self._asset)
        upgrader.run()

        inventory_upgrader.Offering.objects.filter.assert_called_once_with(asset=self._asset)
        inventory_upgrader.Resource.objects.filter.assert_called_once_with(bundled_assets=self._asset_pk)
        self.assertEqual([], self._ctx_instance.failed_upgrades)
        self.assertEqual(0, self._client_instance.get_products.call_count)

        self._check_product_spec_retrieved()

    def test_inventory_upgrader_no_products(self):
        inventory_upgrader.Offering.objects.filter.side_effect = [[MagicMock(off_id=self._product_off_id)], []]
        self._client_instance.get_products.return_value = []

        # Execute the tested method
        upgrader = inventory_upgrader.InventoryUpgrader(self._asset)
        upgrader.run()

        # Check calls
        self.assertEqual([], self._ctx_instance.failed_upgrades)
        self._check_single_get_call()

        self._check_product_spec_retrieved()

    def test_inventory_upgrader(self):
        # Mock assets and offerings
        asset_bundle = MagicMock(bundled_assets=[self._asset.pk])
        inventory_upgrader.Resource.objects.filter.return_value = [asset_bundle]

        offering1 = MagicMock(off_id=self._product_off_id, pk=self._product_off_pk, asset=self._asset)
        offering2 = MagicMock(off_id=self._product_off_id2, pk=self._product_off_pk2, asset=self._asset)
        offering3 = MagicMock(off_id=self._product_off_id3, pk=self._product_off_pk3, asset=asset_bundle)

        inventory_upgrader.Offering.objects.filter.side_effect = [
            # Single offering retrieved from the assets
            [offering1, offering2],
            [offering3],

            # Bundle results
            [MagicMock(off_id=self._off_bundle_id, pk=self._off_bundle_pk)],
            [],
            [MagicMock(off_id=self._off_bundle_id2, pk=self._off_bundle_pk2)],

            # Offering id validation results
            [offering1], [MagicMock()], [offering1], [MagicMock()], [offering1], [MagicMock()],
            [offering3], [offering3], [offering3], [], [], []
        ]

        # Mock inventory client methods
        self._client_instance.get_products.side_effect = [
            [{'id': str(i)} for i in range(1, 6)],  # First call
            [self._product1, self._product2],  # Second call
            [self._product3, self._product4],  # Third call
            [self._product5],  # Last call
            [{'id': str(i)} for i in range(6, 7)],  # First call
            [self._product6],  # Last call
            [{'id': str(i)} for i in range(7, 8)],
            [self._product_p_bundle],
            [{'id': str(i)} for i in range(8, 9)],
            [self._product_off_bundle],
            [{'id': str(i)} for i in range(9, 10)],
            [self._product_mix_bundle]
        ]

        self._client_instance.patch_product.side_effect = [self._product1, self._product2, self._product3,
                                                           self._product4, self._product5, self._product6,
                                                           self._product_p_bundle, self._product_off_bundle,
                                                           self._product_mix_bundle]

        # Execute the tested method
        upgrader = inventory_upgrader.InventoryUpgrader(self._asset)
        upgrader.run()

        inventory_upgrader.Resource.objects.filter.assert_called_once_with(bundled_assets=self._asset_pk)
        self.assertEqual([
            call(asset=self._asset),
            call(asset=asset_bundle),
            call(bundled_offerings=self._product_off_pk),
            call(bundled_offerings=self._product_off_pk2),
            call(bundled_offerings=self._product_off_pk3),
            call(off_id=self._product_off_id),
            call(off_id='asd'),
            call(off_id=self._product_off_id),
            call(off_id='asd'),
            call(off_id=self._product_off_id),
            call(off_id='asd'),
            call(off_id=self._product_off_id3),
            call(off_id=self._product_off_id3),
            call(off_id=self._product_off_id3),
            call(off_id='asd'),
            call(off_id='asd'),
            call(off_id='asd')], inventory_upgrader.Offering.objects.filter.call_args_list)

        # Check calls
        self.assertEqual([], self._ctx_instance.failed_upgrades)

        self.assertEqual([
            call(query={
                'productOffering.id': self._product_off_id,
                'fields': 'id'
            }),
            call(query={
                'id': '1,2',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'id': '3,4',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'id': '5',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'productOffering.id': self._product_off_id2,
                'fields': 'id'
            }),
            call(query={
                'id': '6',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'productOffering.id': self._product_off_id3,
                'fields': 'id'
            }),
            call(query={
                'id': '7',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'productOffering.id': self._off_bundle_id,
                'fields': 'id'
            }),
            call(query={
                'id': '8',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'productOffering.id': self._off_bundle_id2,
                'fields': 'id'
            }),
            call(query={
                'id': '9',
                'fields': 'id,productCharacteristic'
            })
        ], self._client_instance.get_products.call_args_list)

        exp_charp1 = deepcopy(self._new_asset_chars)
        exp_charp1.insert(0, {
            'name': 'speed',
            'value': '100mbps'
        })
        exp_charp2 = deepcopy(self._new_asset_chars)
        exp_charp2.insert(0, {
            'name': 'speed',
            'value': '20mbps'
        })

        self.assertEqual([
            call('1', {
                'productCharacteristic': exp_charp1
            }),
            call('2', {
                'productCharacteristic': exp_charp2
            }),
            call('3', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('4', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('5', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('6', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('7', {
                'productCharacteristic': self._new_product_bundle_chars
            }),
            call('8', {
                'productCharacteristic': self._new_off_bundle_chars
            }),
            call('9', {
                'productCharacteristic': self._new_mixed_bundle_chars
            })
        ], self._client_instance.patch_product.call_args_list)

        self.assertEqual([
            call(order_id='11'),
            call(order_id='22'),
            call(order_id='33'),
            call(order_id='44'),
            call(order_id='55'),
            call(order_id='66'),
            call(order_id='77'),
            call(order_id='88'),
            call(order_id='99')
        ], inventory_upgrader.Order.objects.get.call_args_list)

        self.assertEqual([
            call('1'), call('2'), call('3'), call('4'), call('5'), call('6'), call('7'), call('8'), call('9')
        ], self._order_int.get_product_contract.call_args_list)

        self.assertEqual([call() for i in range(0, 9)], inventory_upgrader.NotificationsHandler.call_args_list)

        self.assertEqual([
            call(self._order_int, self._order_int.get_product_contract(), self._product_spec_name) for i in range(0, 9)
        ], self._not_handler.send_product_upgraded_notification.call_args_list)

        self._check_product_spec_retrieved()

    def test_inventory_upgrader_page_error(self):
        inventory_upgrader.Offering.objects.filter.side_effect = [
            [MagicMock(off_id=self._product_off_id), MagicMock(off_id=self._product_off_id2)], [], []]

        # Mock inventory client methods
        self._client_instance.get_products.side_effect = [
            [{'id': str(i)} for i in range(1, 5)],  # First call off1
            HTTPError(),  # Second call - HTTPError retrieving page
            [self._product3, self._product4],  # Last call off1
            HTTPError()  # Error retrieving second offering
        ]

        self._client_instance.patch_product.side_effect = [self._product3, self._product4]

        self._not_handler.send_product_upgraded_notification.side_effect = Exception()

        # Execute the tested method
        upgrader = inventory_upgrader.InventoryUpgrader(self._asset)
        upgrader.run()

        # Check calls
        self.assertEqual([{
            'asset_id': self._asset_pk,
            'pending_offerings': [self._product_off_id2],
            'pending_products': ['1', '2']
        }], self._ctx_instance.failed_upgrades)
        self._ctx_instance.save.assert_called_once_with()

        inventory_upgrader.DocumentLock.assert_called_once_with('wstore_context', self._ctx_pk, 'ctx')
        self._lock_inst.wait_document.assert_called_once_with()
        self._lock_inst.unlock_document.assert_called_once_with()

        self.assertEqual([
            call(query={
                'productOffering.id': self._product_off_id,
                'fields': 'id'
            }),
            call(query={
                'id': '1,2',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'id': '3,4',
                'fields': 'id,productCharacteristic'
            }),
            call(query={
                'productOffering.id': self._product_off_id2,
                'fields': 'id'
            })
        ], self._client_instance.get_products.call_args_list)

        self.assertEqual([
            call('3', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('4', {
                'productCharacteristic': self._new_asset_chars
            })
        ], self._client_instance.patch_product.call_args_list)

        self.assertEqual([
            call(order_id='33'),
            call(order_id='44'),
        ], inventory_upgrader.Order.objects.get.call_args_list)

        self.assertEqual([call('3'), call('4')], self._order_int.get_product_contract.call_args_list)

        self.assertEqual([call(), call()], inventory_upgrader.NotificationsHandler.call_args_list)

        self.assertEqual([
            call(self._order_int, self._order_int.get_product_contract(), self._product_spec_name),
            call(self._order_int, self._order_int.get_product_contract(), self._product_spec_name),
        ], self._not_handler.send_product_upgraded_notification.call_args_list)

        self._check_product_spec_retrieved()

    def test_inventory_upgrader_patch_error(self):
        inventory_upgrader.Offering.objects.filter.side_effect = [[MagicMock(off_id=self._product_off_id)], []]

        self._client_instance.get_products.side_effect = [
            [{'id': str(i)} for i in range(3, 5)],  # First call
            [self._product3, self._product4],  # Last call
        ]

        self._client_instance.patch_product.side_effect = [None, HTTPError()]

        inventory_upgrader.requests.get.side_effect = HTTPError()

        # Execute the tested method
        upgrader = inventory_upgrader.InventoryUpgrader(self._asset)
        upgrader.run()

        # Check calls
        self.assertEqual([{
            'asset_id': self._asset_pk,
            'pending_offerings': [],
            'pending_products': ['4']
        }], self._ctx_instance.failed_upgrades)
        self._ctx_instance.save.assert_called_once_with()

        inventory_upgrader.DocumentLock.assert_called_once_with('wstore_context', self._ctx_pk, 'ctx')
        self._lock_inst.wait_document.assert_called_once_with()
        self._lock_inst.unlock_document.assert_called_once_with()

        self.assertEqual([
            call(query={
                'productOffering.id': self._product_off_id,
                'fields': 'id'
            }),
            call(query={
                'id': '3,4',
                'fields': 'id,productCharacteristic'
            })
        ], self._client_instance.get_products.call_args_list)

        self.assertEqual([
            call('3', {
                'productCharacteristic': self._new_asset_chars
            }),
            call('4', {
                'productCharacteristic': self._new_asset_chars
            })
        ], self._client_instance.patch_product.call_args_list)

        inventory_upgrader.requests.get.assert_called_once_with(self._product_spec_url)
        self.assertEqual(0, self._resp.raise_for_status.call_count)
        self.assertEqual(0, self._resp.json.call_count)

        self.assertEqual(0, inventory_upgrader.NotificationsHandler.call_count)
