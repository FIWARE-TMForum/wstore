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
from nose_parameterized import parameterized
from mock import MagicMock, call
from datetime import datetime
from urlparse import urlparse

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from wstore.models import Organization
from wstore.ordering.errors import OrderingError
from wstore.ordering.models import Order, Offering, Contract

from wstore.ordering.tests.test_data import *
from wstore.ordering import ordering_client, ordering_management, inventory_client


@override_settings(SITE='http://extpath.com:8080/', VERIFY_REQUESTS=True)
class OrderingManagementTestCase(TestCase):

    tags = ('ordering', 'order-manager')

    def setUp(self):
        self._customer = MagicMock()

        # Mock order model
        ordering_management.Order = MagicMock()
        self._order_inst = MagicMock()
        ordering_management.Order.objects.create.return_value = self._order_inst
        ordering_management.Order.objects.get.return_value = self._order_inst

        # Mock Offering model
        ordering_management.Offering = MagicMock()
        self._offering_inst = MagicMock()
        self._order_inst.bundled_offerings = []
        ordering_management.Offering.objects.filter.return_value = []
        ordering_management.Offering.objects.create.return_value = self._offering_inst

        # Mock Contract model
        ordering_management.Contract = MagicMock()
        self._contract_inst = MagicMock()
        ordering_management.Contract.return_value = self._contract_inst

        # Mock Charging Engine
        ordering_management.ChargingEngine = MagicMock()
        self._charging_inst = MagicMock()
        self._charging_inst.resolve_charging.return_value = 'http://redirectionurl.com/'
        ordering_management.ChargingEngine.return_value = self._charging_inst

        # Mock requests
        ordering_management.requests = MagicMock()
        self._response = MagicMock()
        self._response.status_code = 200
        self._response.json.side_effect = [OFFERING, BILLING_ACCOUNT, CUSTOMER_ACCOUNT, CUSTOMER]
        ordering_management.requests.get.return_value = self._response

        # Mock organization model
        self._org_inst = MagicMock()
        self._org_inst.tax_address = {
            'street': 'fake street'
        }
        ordering_management.Organization = MagicMock()
        ordering_management.Organization.objects.get.return_value = self._org_inst
        self._customer.userprofile.current_organization = self._org_inst
        self._customer.userprofile.access_token = 'example_token'

        # Mock Product validator
        self._validator_inst = MagicMock()
        ordering_management.ProductValidator = MagicMock()
        ordering_management.ProductValidator.return_value = self._validator_inst
        self._validator_inst.parse_characteristics.return_value = ('type', 'media_type', 'http://location.com')

        # Mock Resource
        self._asset_instance = MagicMock()
        ordering_management.Resource = MagicMock()
        ordering_management.Resource.objects.get.return_value = self._asset_instance

        ordering_management.datetime = MagicMock()
        self._now = datetime(2016, 12, 03)
        ordering_management.datetime.utcnow.return_value = self._now

        # Mock offering
        ordering_management.Offering.objects.filter.return_value = [self._offering_inst]
        ordering_management.Offering.objects.get.return_value = self._offering_inst

    def _check_contract_call(self, pricing):
        ordering_management.Contract.assert_called_once_with(
            item_id="1",
            pricing_model=pricing,
            revenue_class="productClass",
            offering=self._offering_inst
        )

    def _check_offering_retrieving_call(self):
        ordering_management.Offering.objects.filter.assert_called_once_with(off_id="5")
        ordering_management.Offering.objects.get.assert_called_once_with(off_id="5")

    def _basic_add_checker(self):
        # Check offering creation
        self._check_offering_retrieving_call()

        # Check contract creation
        self._check_contract_call({
            'general_currency': 'EUR',
            'single_payment': [{
                'value': '12.00',
                'unit': 'one time',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }]
        })

    def _non_digital_add_checker(self):
        self._check_offering_retrieving_call()

    def _recurring_add_checker(self):
        # Check offering creation
        self._check_offering_retrieving_call()

        self._check_contract_call({
            'general_currency': 'EUR',
            'subscription': [{
                'value': '12.00',
                'unit': 'monthly',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }]
        })

    def _usage_add_checker(self):
        self._check_offering_retrieving_call()

        self._check_contract_call({
            'general_currency': 'EUR',
            'pay_per_use': [{
                'value': '12.00',
                'unit': 'megabyte',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }]
        })

    def _free_add_checker(self):
        self._check_offering_retrieving_call()
        self._check_contract_call({})

    def _basic_discount_checker(self):
        self._check_offering_retrieving_call()
        self._check_contract_call({
            'general_currency': 'EUR',
            'pay_per_use': [{
                'value': '12.00',
                'unit': 'megabyte',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }],
            'alteration': {
                'type': 'discount',
                'period': 'one time',
                'value': 50
            }
        })

    def _recurring_fee_checker(self):
        self._check_offering_retrieving_call()
        self._check_contract_call({
            'general_currency': 'EUR',
            'pay_per_use': [{
                'value': '12.00',
                'unit': 'megabyte',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }],
            'alteration': {
                'type': 'fee',
                'period': 'recurring',
                'value': {
                    'value': '1.00',
                    'duty_free': '0.80'
                },
                'condition': {
                    'operation': 'gt',
                    'value': '300.00'
                }
            }
        })

    def _double_price_checker(self):
        self._check_offering_retrieving_call()
        self._check_contract_call({
            'general_currency': 'EUR',
            'pay_per_use': [{
                'value': '12.00',
                'unit': 'megabyte',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }],
            'single_payment': [{
                'value': '8.00',
                'unit': 'one time',
                'tax_rate': '20.00',
                'duty_free': '6.00'
            }]
        })

    def _double_usage_checker(self):
        self._check_offering_retrieving_call()
        self._check_contract_call({
            'general_currency': 'EUR',
            'pay_per_use': [{
                'value': '12.00',
                'unit': 'megabyte',
                'tax_rate': '20.00',
                'duty_free': '10.00'
            }, {
                'value': '8.00',
                'unit': 'second',
                'tax_rate': '20.00',
                'duty_free': '6.00'
            }]
        })

    def _invalid_billing(self):
        valid_response = MagicMock()
        valid_response.status_code = 200
        valid_response.json.side_effect = [OFFERING]
        invalid_response = MagicMock()
        invalid_response.status_code = 400
        ordering_management.requests.get.side_effect = [valid_response, invalid_response]

    def _non_digital_offering(self):
        self._validator_inst.parse_characteristics.return_value = (None, None, None)

    def _no_offering_description(self):
        new_off = deepcopy(OFFERING)
        del(new_off['description'])
        self._response.json.side_effect = [new_off, BILLING_ACCOUNT, CUSTOMER_ACCOUNT, CUSTOMER]

    def _missing_offering(self):
        self._response.status_code = 404

    def _missing_product(self):
        def get(url):
            result = self._response
            if url == "http://producturl.com/":
                result = MagicMock()
                result.status_code = 404
            return result

        ordering_management.requests.get = get

    def _already_owned(self):
        self._offering_inst.pk = '11111'
        self._offering_inst.name = 'Example offering'
        self._offering_inst.off_id = '5'
        self._customer.userprofile.current_organization.acquired_offerings = ['11111']

    def _already_owned_bundle(self):
        bundle_offering = MagicMock()
        bundle_offering.pk = '111111'
        bundle_offering.name = 'Bundle'
        bundle_offering.off_id = '6'
        self._offering_inst.bundled_offerings = ['111111']
        self._customer.userprofile.current_organization.acquired_offerings = ['111111']

        ordering_management.Offering.objects.get.side_effect = [self._offering_inst, bundle_offering]

    def _multiple_pricing(self):
        OFFERING['productOfferingPrice'].append(BASIC_PRICING)

    def _missing_offering_local(self):
        ordering_management.Offering.objects.filter.return_value = []

    def _missing_postal(self):
        new_cust = deepcopy(CUSTOMER)
        new_cust['contactMedium'] = []
        self._response.json.side_effect = [OFFERING, BILLING_ACCOUNT, CUSTOMER_ACCOUNT, new_cust]

    def _terms_not_required(self):
        self._contract_inst.offering.asset.has_terms = False

    @parameterized.expand([
        ('basic_add', BASIC_ORDER, BASIC_PRICING, _basic_add_checker),
        ('basic_add_terms_not_accepted', BASIC_ORDER, BASIC_PRICING, None, None, 'OrderingError: You must accept the terms and conditions of the offering to acquire it', False),
        ('basic_add_terms_not_required', BASIC_ORDER, BASIC_PRICING, _basic_add_checker, _terms_not_required, None, False),
        ('basic_add_invalid_billing', BASIC_ORDER, BASIC_PRICING, None, _invalid_billing, 'OrderingError: There was an error at the time of retrieving the Billing Address'),
        ('non_digital_add', BASIC_ORDER, BASIC_PRICING, _non_digital_add_checker, _non_digital_offering),
        ('recurring_add', RECURRING_ORDER, RECURRING_PRICING, _recurring_add_checker),
        ('usage_add', USAGE_ORDER, USAGE_PRICING, _usage_add_checker, _no_offering_description),
        ('free_add', FREE_ORDER, {}, _free_add_checker),
        ('no_product_add', NOPRODUCT_ORDER, {}, _free_add_checker),
        ('discount', USAGE_ORDER, DISCOUNT_PRICING, _basic_discount_checker, _multiple_pricing),
        ('recurring_fee', USAGE_ORDER, RECURRING_FEE_PRICING, _recurring_fee_checker),
        ('double_price', USAGE_ORDER, DOUBLE_PRICE_PRICING, _double_price_checker),
        ('double_price_usage', USAGE_ORDER, DOUBLE_USAGE_PRICING, _double_usage_checker),
        ('pricing_not_found', USAGE_ORDER, BASIC_PRICING, None, None, 'OrderingError: The product price included in orderItem 1 does not match with any of the prices included in the related offering'),
        ('multiple_pricing', BASIC_ORDER, BASIC_PRICING, None, _multiple_pricing, 'OrderingError: The product price included in orderItem 1 matches with multiple pricing models of the related offering'),
        ('invalid_alt', USAGE_ORDER, INV_ALTERATION_PRICING, None, None, 'OrderingError: Invalid price alteration, it is not possible to determine if it is a discount or a fee'),
        ('usage_alteration', USAGE_ORDER, USAGE_ALTERATION_PRICING, None, None, 'OrderingError: Invalid priceType in price alteration, it must be one time or recurring'),
        ('inv_alteration_cond', USAGE_ORDER, INV_CONDITION_PRICING, None, None, 'OrderingError: Invalid priceCondition in price alteration, format must be: [eq | lt | gt | le | ge] value'),
        ('invalid_initial_state', INVALID_STATE_ORDER, BASIC_PRICING,  None, None, 'OrderingError: Only acknowledged orders can be initially processed'),
        ('invalid_model', INVALID_MODEL_ORDER, INVALID_MODEL_PRICING,  None, None, 'OrderingError: Invalid price model Invalid'),
        ('invalid_offering', BASIC_ORDER, {}, None, _missing_offering, 'OrderingError: The product offering specified in order item 1 does not exists'),
        ('already_owned', BASIC_ORDER, {}, None, _already_owned, 'OrderingError: The customer already owns the digital product offering Example offering with id 5'),
        ('already_owned_bundle', BASIC_ORDER, {}, None, _already_owned_bundle, 'OrderingError: The customer already owns the digital product offering Bundle with id 6'),
        ('offering_not_registered', BASIC_ORDER, {}, None, _missing_offering_local, 'OrderingError: The offering 5 has not been previously registered'),
        ('missing_postal_address', BASIC_ORDER, BASIC_PRICING, None, _missing_postal, 'OrderingError: Provided Billing Account does not contain a Postal Address')
    ])
    def test_process_order(self, name, order, pricing, checker, side_effect=None, err_msg=None, terms_accepted=True):

        OFFERING['productOfferingPrice'] = [pricing]

        if side_effect is not None:
            side_effect(self)

        ordering_manager = ordering_management.OrderingManager()
        error = None
        try:
            redirect_url = ordering_manager.process_order(self._customer, order, terms_accepted=terms_accepted)
        except OrderingError as e:
            error = e

        if err_msg is None:
            self.assertTrue(error is None)

            # Check returned value
            self.assertEquals('http://redirectionurl.com/', redirect_url)

            # Check common calls
            ordering_management.ChargingEngine.assert_called_once_with(self._order_inst)

            # Check offering and product downloads
            self.assertEquals(4, ordering_management.requests.get.call_count)

            headers = {'Authorization': 'Bearer ' + self._customer.userprofile.access_token}
            exp_url = 'http://extpath.com:8080{}'
            self.assertEquals([
                call(exp_url.format('/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)'), verify=True),
                call(exp_url.format(urlparse(BILLING_ACCOUNT_HREF).path), headers=headers, verify=True),
                call(exp_url.format(urlparse(BILLING_ACCOUNT['customerAccount']['href']).path), headers=headers, verify=True),
                call(exp_url.format(urlparse(CUSTOMER_ACCOUNT['customer']['href']).path), headers=headers, verify=True)
            ], ordering_management.requests.get.call_args_list)

            contact_medium = CUSTOMER['contactMedium'][0]['medium']

            ordering_management.Order.objects.create.assert_called_once_with(
                order_id="12",
                customer=self._customer,
                owner_organization=self._org_inst,
                date=self._now,
                state='pending',
                tax_address={
                    'street': contact_medium['streetOne'] + '\n' + contact_medium['streetTwo'],
                    'postal': contact_medium['postcode'],
                    'city': contact_medium['city'],
                    'province': contact_medium['stateOrProvince'],
                    'country': contact_medium['country']
                },
                contracts=[self._contract_inst],
                description=""
            )

            # Check particular calls
            checker(self)
        else:
            self.assertEquals(err_msg, unicode(error))

    BASIC_MODIFY = {
        'state': 'Acknowledged',
        'orderItem': [{
            'id': '1',
            'action': 'modify',
            'product': {
                'id': '89'
            }
        }]
    }


    @parameterized.expand([
        ('basic_modify', BASIC_MODIFY, {
            'subscription': [{
                'renovation_date': datetime(2016, 1, 1)
            }]
        }, 'new_pricing'),
        ('empty_pricing', BASIC_MODIFY, {}, {}),
        ('mix_error', {
            'state': 'Acknowledged',
            'orderItem': [{
                'action': 'modify'
            }, {
                'action': 'add'
            }]
        }, {}, {}, 'OrderingError: It is not possible to process add and modify items in the same order'),
        ('multiple_mod', {
            'state': 'Acknowledged',
            'orderItem': [{
                'action': 'modify'
            }, {
                'action': 'modify'
            }]
        }, {}, {}, 'OrderingError: Only a modify item is supported per order item'),
        ('missing_product', {
            'state': 'Acknowledged',
            'orderItem': [{
                'action': 'modify'
            }]
        }, {}, {}, 'OrderingError: It is required to specify product information in modify order items'),
        ('missing_product_id', {
            'state': 'Acknowledged',
            'orderItem': [{
                'action': 'modify',
                'product': {
                }
            }]
        }, {}, {}, 'OrderingError: It is required to provide product id in modify order items'),
        ('product_not_exp', BASIC_MODIFY, {
            'subscription': [{
                'renovation_date': datetime(2050, 1, 1)
            }]
        }, {}, 'OrderingError: You cannot modify a product with a recurring payment until the subscription expires')
    ])
    def test_modify_order(self, name, order, pricing, new_pricing, err_msg=None):
        # Mock order method
        mock_contract = MagicMock()
        mock_contract.pricing_model = pricing
        mock_contract.revenue_class = 'old_revenue'
        self._order_inst.get_product_contract.return_value = mock_contract

        ordering_management.InventoryClient = MagicMock()
        ordering_management.InventoryClient().get_product.return_value = {'id': '1', 'name': 'oid=35'}

        ordering = ordering_management.OrderingManager()
        ordering._build_contract = MagicMock()
        new_contract = MagicMock()
        new_contract.pricing_model = new_pricing
        new_contract.revenue_class = 'new_revenue'
        ordering._build_contract.return_value = new_contract

        error = None
        try:
            ordering.process_order(self._customer, order)
        except OrderingError as e:
            error = e

        if err_msg is None:
            self.assertTrue(error is None)

            ordering_management.InventoryClient().get_product.assert_called_once_with('89')
            ordering_management.Order.objects.get.assert_called_once_with(order_id='35')

            self._order_inst.get_product_contract.assert_called_once_with('89')

            ordering._build_contract.assert_called_once_with({
                'id': '1',
                'action': 'modify',
                'product': {
                    'id': '89'
                }
            })
            ordering_management.ChargingEngine.assert_called_once_with(self._order_inst)
            self._charging_inst.resolve_charging.assert_called_once_with(type_='initial', related_contracts=[mock_contract])

            if new_pricing != {}:
                self.assertEquals(new_pricing, mock_contract.pricing_model)
                self.assertEquals('new_revenue', mock_contract.revenue_class)
            else:
                self.assertEquals(pricing, mock_contract.pricing_model)
                self.assertEquals('old_revenue', mock_contract.revenue_class)
        else:
            self.assertEquals(err_msg, unicode(error))


@override_settings(
    ORDERING='http://localhost:8080/DSProductOrdering'
)
class OrderingClientTestCase(TestCase):

    tags = ('ordering', 'ordering-client')

    def setUp(self):
        ordering_client.settings.LOCAL_SITE = 'http://testdomain.com'

        # Mock requests
        ordering_client.requests = MagicMock()
        self._response = MagicMock()
        self._response.status_code = 200
        self._response.json.return_value = {
            'id': '1'
        }
        ordering_client.requests.post.return_value = self._response
        ordering_client.requests.patch.return_value = self._response
        ordering_client.requests.get.return_value = self._response

    def test_ordering_subscription(self):
        client = ordering_client.OrderingClient()

        client.create_ordering_subscription()

        # Check calls
        ordering_client.requests.post.assert_called_once_with('http://localhost:8080/DSProductOrdering/productOrdering/v2/hub', {
            'callback': 'http://testdomain.com/charging/api/orderManagement/orders'
        })

    def test_ordering_subscription_error(self):
        client = ordering_client.OrderingClient()
        self._response.status_code = 400

        error = None
        try:
            client.create_ordering_subscription()
        except ImproperlyConfigured as e:
            error = e

        self.assertFalse(error is None)
        msg = "It hasn't been possible to create ordering subscription, "
        msg += 'please check that the ordering API is correctly configured '
        msg += 'and that the ordering API is up and running'

        self.assertEquals(msg, unicode(e))

    @parameterized.expand([
        ('complete', {
            'orderItem': [{
                'id': '1',
                'state': 'InProgress'
            }, {
                'id': '2',
                'state': 'InProgress'
            }]
        }),
        ('partial', {
            'orderItem': [{
                'id': '1',
                'state': 'Acknowledged'
            }, {
                'id': '2',
                'state': 'InProgress'
            }]
        }, [{'id': '2'}])
    ])
    def test_update_items_state(self, name, expected, items=None):
        client = ordering_client.OrderingClient()
        order = {
            'id': '20',
            'orderItem': [{
                'id': '1',
                'state': 'Acknowledged'
            }, {
                'id': '2',
                'state': 'Acknowledged'
            }]
        }
        client.update_items_state(order, 'InProgress', items)

        ordering_client.requests.patch.assert_called_once_with(
            'http://localhost:8080/DSProductOrdering/api/productOrdering/v2/productOrder/20',
            json=expected)

        self._response.raise_for_status.assert_called_once_with()

    def test_update_state(self):
        client = ordering_client.OrderingClient()
        new_state = 'Failed'

        order = {
            'id': '7'
        }

        client.update_state(order, new_state)

        ordering_client.requests.patch.assert_called_once_with(
            'http://localhost:8080/DSProductOrdering/api/productOrdering/v2/productOrder/' + order['id'],
            json={'state': new_state})

        self._response.raise_for_status.assert_called_once_with()

    def test_get_order(self):
        client = ordering_client.OrderingClient()

        response = client.get_order('1')

        self.assertEquals({
            'id': '1'
        }, response)

        ordering_client.requests.get.assert_called_once_with(
            'http://localhost:8080/DSProductOrdering/api/productOrdering/v2/productOrder/1'
        )
        self._response.raise_for_status.assert_called_once_with()


class OrderTestCase(TestCase):

    tags = ('ordering', )

    def setUp(self):
        # Build users and organizations
        customer = User.objects.create_user('test_user')

        owner_org = Organization.objects.create(name='test_org')

        # Build offerings and contracts
        offering1 = Offering(
            off_id='1',
            owner_organization=owner_org,
            name='Offering1',
            version='1.0',
            description='Offering1'
        )

        offering2 = Offering(
            off_id='2',
            owner_organization=owner_org,
            name='Offering2',
            version='1.0',
            description='Offering2'
        )

        self._contract1 = Contract(
            item_id='1',
            product_id='3',
            offering=offering1,
        )

        self._contract2 = Contract(
            item_id='2',
            product_id='4',
            offering=offering2,
        )

        # Build order
        self._order = Order.objects.create(
            description='',
            order_id='1',
            date=datetime.utcnow(),
            customer=customer,
            state='pending',
            contracts=[self._contract1, self._contract2]
        )

    def test_get_item_contract(self):
        contract = self._order.get_item_contract('2')
        self.assertEquals(self._contract2, contract)

    def test_get_item_contract_invalid(self):
        error = None
        try:
            self._order.get_item_contract('3')
        except OrderingError as e:
            error = e

        self.assertFalse(error is None)
        self.assertEquals('OrderingError: Invalid item id', unicode(e))

    def test_get_product(self):
        contract = self._order.get_product_contract('4')
        self.assertEquals(self._contract2, contract)

    def test_get_product_invalid(self):
        error = None
        try:
            self._order.get_product_contract('1')
        except OrderingError as e:
            error = e

        self.assertFalse(error is None)
        self.assertEquals('OrderingError: Invalid product id', unicode(e))


@override_settings(
    INVENTORY='http://localhost:8080/DSProductInventory'
)
class InventoryClientTestCase(TestCase):

    tags = ('inventory', )

    def setUp(self):
        # Mock requests
        inventory_client.requests = MagicMock()
        self.response = MagicMock()
        self.response.status_code = 201
        inventory_client.requests.post.return_value = self.response
        inventory_client.requests.get.return_value = self.response

        inventory_client.settings.LOCAL_SITE = 'http://localhost:8004/'

        from datetime import datetime
        now = datetime(2016, 1, 22, 4, 10, 25, 176751)
        inventory_client.datetime = MagicMock()
        inventory_client.datetime.utcnow.return_value = now

    @parameterized.expand([
        ('basic', [{
            'callback': 'http://site.com/event'
        }]),
        ('initial', []),
        ('registered', [{
            'callback': 'http://site.com/event'
        }, {
            'callback': 'http://localhost:8004/charging/api/orderManagement/products'
        }], False),
    ])
    def test_create_subscription(self, name, callbacks, created=True):

        self.response.json.return_value = callbacks

        client = inventory_client.InventoryClient()
        client.create_inventory_subscription()

        inventory_client.requests.get.assert_called_once_with('http://localhost:8080/DSProductInventory/api/productInventory/v2/hub')

        if created:
            inventory_client.requests.post.assert_called_once_with(
                'http://localhost:8080/DSProductInventory/api/productInventory/v2/hub',
                json={
                    'callback': 'http://localhost:8004/charging/api/orderManagement/products'
                }
            )
        else:
            self.assertEquals(0, inventory_client.requests.post.call_count)

    def test_create_subscription_error(self):
        self.response.json.return_value = []
        self.response.status_code = 404

        error = None
        try:
            client = inventory_client.InventoryClient()
            client.create_inventory_subscription()
        except ImproperlyConfigured as e:
            error = e

        self.assertTrue(isinstance(error, ImproperlyConfigured))
        msg = "It hasn't been possible to create inventory subscription, "
        msg += 'please check that the inventory API is correctly configured '
        msg += 'and that the inventory API is up and running'
        self.assertEquals(msg, unicode(error))

    def test_activate_product(self):
        client = inventory_client.InventoryClient()
        client.activate_product('1')

        inventory_client.requests.patch.assert_called_once_with('http://localhost:8080/DSProductInventory/api/productInventory/v2/product/1', json={
            'status': 'Active',
            'startDate': '2016-01-22T04:10:25.176751Z'
        })
        inventory_client.requests.patch().raise_for_status.assert_called_once_with()

    def test_suspend_product(self):
        client = inventory_client.InventoryClient()
        client.suspend_product('1')

        inventory_client.requests.patch.assert_called_once_with('http://localhost:8080/DSProductInventory/api/productInventory/v2/product/1', json={
            'status': 'Suspended'
        })
        inventory_client.requests.patch().raise_for_status.assert_called_once_with()

    def test_terminate_product(self):
        client = inventory_client.InventoryClient()
        client.terminate_product('1')

        self.assertEquals([
            call('http://localhost:8080/DSProductInventory/api/productInventory/v2/product/1', json={
                'status': 'Active',
                'startDate': '2016-01-22T04:10:25.176751Z'
            }),
            call('http://localhost:8080/DSProductInventory/api/productInventory/v2/product/1', json={
                'status': 'Terminated',
                'terminationDate': '2016-01-22T04:10:25.176751Z'
            })
        ], inventory_client.requests.patch.call_args_list)

        self.assertEquals([call(), call()], inventory_client.requests.patch().raise_for_status.call_args_list)

    def test_get_product(self):
        client = inventory_client.InventoryClient()
        client.get_product('1')

        inventory_client.requests.get.assert_called_once_with('http://localhost:8080/DSProductInventory/api/productInventory/v2/product/1')
        inventory_client.requests.get().raise_for_status.assert_called_once_with()

    @parameterized.expand([
        ('all', {}, ''),
        ('filtered', {'id': '1,2,3'}, '?id=1,2,3')
    ])
    def test_get_products(self, name, query, qs):
        client = inventory_client.InventoryClient()
        products = client.get_products(query=query)

        inventory_client.requests.get.assert_called_once_with('http://localhost:8080/DSProductInventory/api/productInventory/v2/product' + qs)
        inventory_client.requests.get().raise_for_status.assert_called_once_with()

        self.assertEquals(inventory_client.requests.get().json(), products)
