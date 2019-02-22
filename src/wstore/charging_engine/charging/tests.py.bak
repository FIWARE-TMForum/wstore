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

from bson.objectid import ObjectId
from decimal import Decimal
from datetime import datetime
from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase

from wstore.charging_engine.charging import billing_client, cdr_manager

INITIAL_EXP = [{
    'provider': 'provider',
    'correlation': '1',
    'order': '1 3',
    'offering': '4 offering 1.0',
    'product_class': 'one time',
    'description': 'One time payment: 12 EUR',
    'cost_currency': 'EUR',
    'cost_value': '12',
    'tax_value': '2',
    'customer': 'customer',
    'event': 'One time payment event',
    'time_stamp': u'2015-10-21 06:13:26.661650',
    'type': 'C'
}]

RECURRING_EXP = [{
    'provider': 'provider',
    'correlation': '1',
    'order': '1 3',
    'offering': '4 offering 1.0',
    'product_class': 'one time',
    'description': 'Recurring payment: 12 EUR monthly',
    'cost_currency': 'EUR',
    'cost_value': '12',
    'tax_value': '2',
    'customer': 'customer',
    'event': 'Recurring payment event',
    'time_stamp': u'2015-10-21 06:13:26.661650',
    'type': 'C'
}]

USAGE_EXP = [{
    'provider': 'provider',
    'correlation': '1',
    'order': '1 3',
    'offering': '4 offering 1.0',
    'product_class': 'one time',
    'description': 'Fee per invocation, Consumption: 25',
    'cost_currency': 'EUR',
    'cost_value': '25.0',
    'tax_value': '5.0',
    'customer': 'customer',
    'event': 'Pay per use event',
    'time_stamp': u'2015-10-21 06:13:26.661650',
    'type': 'C'
}]


class CDRGenerationTestCase(TestCase):

    tags = ('cdr', )

    def setUp(self):
        # Create Mocks
        cdr_manager.RSSAdaptorThread = MagicMock()

        self._conn = MagicMock()
        cdr_manager.get_database_connection = MagicMock()
        cdr_manager.get_database_connection.return_value = self._conn

        self._conn.wstore_organization.find_and_modify.side_effect = [{'correlation_number': 1}, {'correlation_number': 2}]

        self._order = MagicMock()
        self._order.order_id = '1'
        self._order.owner_organization.name = 'customer'

        self._contract = MagicMock()
        self._contract.revenue_class = 'one time'
        self._contract.offering.off_id = '2'
        self._contract.item_id = '3'
        self._contract.pricing_model = {
            'general_currency': 'EUR'
        }
        self._contract.offering.off_id = '4'
        self._contract.offering.name = 'offering'
        self._contract.offering.version = '1.0'
        self._contract.offering.owner_organization.name = 'provider'
        self._contract.offering.owner_organization.pk = '61004aba5e05acc115f022f0'

    @parameterized.expand([
        ('initial_charge', {
             'single_payment': [{
                'value': Decimal('12'),
                'unit': 'one time',
                'tax_rate': Decimal('20'),
                'duty_free': Decimal('10')
             }]
         }, INITIAL_EXP),
        ('recurring_charge', {
             'subscription': [{
                'value': Decimal('12'),
                'unit': 'monthly',
                'tax_rate': Decimal('20'),
                'duty_free': Decimal('10')
             }]
         }, RECURRING_EXP),
        ('usage', {
            'accounting': [{
                'accounting': [{
                    'order_id': '1',
                    'product_id': '1',
                    'customer': 'customer',
                    'value': '15',
                    'unit': 'invocation'
                }, {
                    'order_id': '1',
                    'product_id': '1',
                    'customer': 'customer',
                    'value': '10',
                    'unit': 'invocation'
                }],
                'model': {
                    'unit': 'invocation',
                    'currency': 'EUR',
                    'value': '1'
                },
                'price': Decimal('25.0'),
                'duty_free': Decimal('20.0')
             }]
        }, USAGE_EXP)
    ])
    def test_cdr_generation(self, name, applied_parts, exp_cdrs):

        cdr_m = cdr_manager.CDRManager(self._order, self._contract)
        cdr_m.generate_cdr(applied_parts, '2015-10-21 06:13:26.661650')

        # Validate calls
        self._conn.wstore_organization.find_and_modify.assert_called_once_with(
            query={'_id': ObjectId('61004aba5e05acc115f022f0')},
            update={'$inc': {'correlation_number': 1}}
        )

        cdr_manager.RSSAdaptorThread.assert_called_once_with(exp_cdrs)
        cdr_manager.RSSAdaptorThread().start.assert_called_once_with()

    def test_refund_cdr_generation(self):
        exp_cdr = [{
            'provider': 'provider',
            'correlation': '1',
            'order': '1 3',
            'offering': '4 offering 1.0',
            'product_class': 'one time',
            'description': 'Refund event: 10 EUR',
            'cost_currency': 'EUR',
            'cost_value': '10',
            'tax_value': '2',
            'customer': 'customer',
            'event': 'Refund event',
            'time_stamp': u'2015-10-21 06:13:26.661650',
            'type': 'R'
        }]

        cdr_m = cdr_manager.CDRManager(self._order, self._contract)
        cdr_m.refund_cdrs(Decimal('10'), Decimal('8'), '2015-10-21 06:13:26.661650')

        # Validate calls
        self._conn.wstore_organization.find_and_modify.assert_called_once_with(
            query={'_id': ObjectId('61004aba5e05acc115f022f0')},
            update={'$inc': {'correlation_number': 1}}
        )

        cdr_manager.RSSAdaptorThread.assert_called_once_with(exp_cdr)
        cdr_manager.RSSAdaptorThread().start.assert_called_once_with()


TIMESTAMP = datetime(2016, 06, 21, 10, 0, 0)
RENEW_DATE = datetime(2016, 07, 21, 10, 0, 0)
START_DATE = datetime(2016, 05, 21, 10, 0, 0)

COMMON_CHARGE = {
    'date': TIMESTAMP.isoformat() + 'Z',
    'currencyCode': 'EUR',
    'taxIncludedAmount': '10',
    'taxExcludedAmount': '8',
    'appliedCustomerBillingTaxRate': [{
        'amount': '20',
        'taxCategory': 'VAT'
    }],
    'serviceId': [{
        'id': '1',
        'type': 'Inventory product'
    }]
}

BASIC_CHARGE = {
    'description': 'initial charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf',
    'type': 'initial'
}
BASIC_CHARGE.update(COMMON_CHARGE)

RECURRING_CHARGE = {
    'description': 'recurring charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf',
    'type': 'recurring',
    'period': [{
        'startPeriod': TIMESTAMP.isoformat() + 'Z',
        'endPeriod': RENEW_DATE.isoformat() + 'Z'
    }]
}
RECURRING_CHARGE.update(COMMON_CHARGE)

USAGE_CHARGE = {
    'description': 'usage charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf',
    'type': 'usage',
    'period': [{
        'startPeriod': START_DATE.isoformat() + 'Z',
        'endPeriod': TIMESTAMP.isoformat() + 'Z'
    }]
}
USAGE_CHARGE.update(COMMON_CHARGE)


class BillingClientTestCase(TestCase):

    tags = ('billing', )

    @parameterized.expand([
        ('initial', None, None, BASIC_CHARGE),
        ('recurring', None, RENEW_DATE, RECURRING_CHARGE),
        ('usage', START_DATE, None, USAGE_CHARGE)
    ])
    def test_create_charge(self, name, start_date, end_date, exp_body):
        # Create Mocks
        billing_client.settings.BILLING = 'http://billing.api.com'

        charge = MagicMock()
        charge.date = TIMESTAMP
        charge.cost = '10'
        charge.duty_free = '8'
        charge.invoice = 'charging/media/bills/bill1.pdf'
        charge.currency = 'EUR'
        charge.concept = name

        site = 'http://extpath.com:8080/'
        billing_client.settings.SITE = site

        billing_client.Request = MagicMock()
        billing_client.Session = MagicMock()
        session = MagicMock()
        billing_client.Session.return_value = session

        preped = MagicMock()
        preped.headers = {}
        session.prepare_request.return_value = preped

        # Call the method to test
        client = billing_client.BillingClient()
        client.create_charge(charge, '1', start_date=start_date, end_date=end_date)

        # Validate calls
        billing_client.Request.assert_called_once_with(
            'POST',
            'http://billing.api.com/api/billingManagement/v2/appliedCustomerBillingCharge',
            json=exp_body
        )

        billing_client.Session.assert_called_once_with()
        session.prepare_request.assert_called_once_with(billing_client.Request())

        self.assertEquals(
            'extpath.com:8080',
            preped.headers['Host']
        )

        session.send.assert_called_once_with(preped)
        session.send().raise_for_status.assert_called_once_with()
