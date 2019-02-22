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

from __future__ import unicode_literals

from bson import ObjectId

from copy import deepcopy
from mock import MagicMock
from mock import call
from nose_parameterized import parameterized

from django.test import TestCase
from django.conf import settings

from wstore.rss_adaptor import rss_adaptor, rss_manager, model_manager


class RSSAdaptorTestCase(TestCase):

    tags = ('rss-adaptor',)

    def setUp(self):
        settings.WSTOREMAIL = 'testmail@mail.com'
        settings.RSS = 'http://testhost.com/rssHost/'
        settings.STORE_NAME = 'wstore'

        rss_adaptor.requests = MagicMock()
        self._response = MagicMock()
        rss_adaptor.requests.post.return_value = self._response

        # Mocks for fail responses
        rss_adaptor.get_database_connection = MagicMock()
        rss_adaptor.Organization = MagicMock()
        rss_adaptor.Organization.objects.get().pk = b"111111111111"
        rss_adaptor.Context = MagicMock()

    def test_rss_client(self):
        # Create mocks
        self._response.status_code = 201

        rss_ad = rss_adaptor.RSSAdaptor()

        rss_ad.send_cdr([{
            'provider': 'test_provider',
            'correlation': '2',
            'order': '1234567890',
            'offering': 'test_offering',
            'product_class': 'SaaS',
            'description': 'The description',
            'cost_currency': 'EUR',
            'cost_value': '10',
            'tax_value': '0.0',
            'time_stamp': '10-05-13T10:00:00Z',
            'customer': 'test_customer',
            'event': 'One time',
            'type': 'C'
        }])

        rss_adaptor.requests.post.assert_called_once_with(
            'http://testhost.com/rssHost/rss/cdrs', json=[{
                'cdrSource': 'testmail@mail.com',
                'productClass': 'SaaS',
                'correlationNumber': '2',
                'timestamp': '10-05-13T10:00:00Z',
                'application': 'test_offering',
                'transactionType': 'C',
                'event': 'One time',
                'referenceCode': '1234567890',
                'description': 'The description',
                'chargedAmount': '10',
                'chargedTaxAmount': '0.0',
                'currency': 'EUR',
                'customerId': 'test_customer',
                'appProvider': 'test_provider'
            }],
            headers={
                'content-type': 'application/json',
                'X-Nick-Name': 'wstore',
                'X-Roles': 'provider',
                'X-Email': 'testmail@mail.com'
            })

        rss_adaptor.get_database_connection.assert_not_called()
        rss_adaptor.Context.objects.all.assert_not_called()

    def test_rss_remote_error(self):
        # Create Mocks
        self._response.status_code = 500

        cdr = {
            'provider': 'test_provider',
            'correlation': '2',
            'order': '1234567890',
            'offering': 'test_offering',
            'product_class': 'SaaS',
            'description': 'The description',
            'cost_currency': 'EUR',
            'cost_value': '10',
            'tax_value': '0.0',
            'time_stamp': '10-05-13T10:00:00Z',
            'customer': 'test_customer',
            'event': 'One time',
            'type': 'C'
        }
        cdrs = [cdr, cdr]

        rss_ad = rss_adaptor.RSSAdaptor()
        rss_ad.send_cdr(cdrs)

        # Decrement correlation number for every cdr
        calls = call(query={'_id': ObjectId(b"111111111111")}, update={'$inc': {'correlation_number': -1}})
        rss_adaptor.get_database_connection().wstore_organization.find_and_modify.assert_has_calls([calls, calls], any_order=True)
        # Save the failed cdrs
        rss_adaptor.Context.objects.all.assert_called_once_with()
        rss_adaptor.Context.objects.all()[0].failed_cdrs.extend.assert_called_once_with(cdrs)
        rss_adaptor.Context.objects.all()[0].save.assert_called_once_with()


BASIC_MODEL = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 30,
    'productClass': 'class'
}

ST_MODEL = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 30,
    'productClass': 'class',
    'stakeholders': []
}

MISSING_OWNER_VAL = {
    'ownerProviderId': 'provider',
    'aggregatorValue': 30,
    'productClass': 'class'
}

INV_OWNER_VAL = {
    'ownerProviderId': 'provider',
    'ownerValue': 'invalid',
    'aggregatorValue': 30,
    'productClass': 'class'
}

INV_AGG_VAL = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 'invalid',
    'productClass': 'class'
}

MISSING_AGG_VAL = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'productClass': 'class'
}

INV_PERCENTAGE = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 120,
    'productClass': 'class'
}

MISSING_PROV = {
    'ownerValue': 70,
    'aggregatorValue': 30,
    'productClass': 'class'
}

INV_PROV = {
    'ownerProviderId': 20,
    'ownerValue': 70,
    'aggregatorValue': 30,
    'productClass': 'class'
}

MISSING_CLASS = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 30,
}

INV_CLASS = {
    'ownerProviderId': 'provider',
    'ownerValue': 70,
    'aggregatorValue': 30,
    'productClass': 20
}

EXP_BASIC_MODEL = {
    'aggregatorId': 'testmail@mail.com',
    'ownerProviderId': 'provider',
    'ownerValue': '70',
    'aggregatorValue': '30',
    'productClass': 'class',
    'algorithmType': 'FIXED_PERCENTAGE',
    'stakeholders': []
}


class ModelManagerTestCase(TestCase):

    tags = ('rs-models', )

    @classmethod
    def tearDownClass(cls):
        reload(rss_manager)
        super(ModelManagerTestCase, cls).tearDownClass()

    def setUp(self):
        settings.WSTOREMAIL = 'testmail@mail.com'
        settings.RSS = 'http://testhost.com/rssHost/'
        settings.STORE_NAME = 'wstore'

        # Create Mocks
        self.manager = model_manager.ModelManager({})
        self.manager._make_request = MagicMock()
        TestCase.setUp(self)

    @parameterized.expand([
        ('correct', BASIC_MODEL, EXP_BASIC_MODEL),
        ('with_stakeholders', ST_MODEL, EXP_BASIC_MODEL),
        ('missing_owner_value', MISSING_OWNER_VAL, None, ValueError, 'Missing a required field in model info: ownerValue'),
        ('invalid_owner_value', INV_OWNER_VAL, None, TypeError, 'Invalid type for ownerValue field'),
        ('missing_aggregator_value', MISSING_AGG_VAL, None, ValueError, 'Missing a required field in model info: aggregatorValue'),
        ('inv_perc_aggregator_value', INV_PERCENTAGE, None, ValueError, 'aggregatorValue must be a number between 0 and 100'),
        ('invalid_aggregator_value', INV_AGG_VAL, None, TypeError, 'Invalid type for aggregatorValue field'),
        ('missing_provider', MISSING_PROV, None, ValueError, 'Missing a required field in model info: ownerProviderId'),
        ('invalid_provider_type', INV_PROV, None, TypeError, 'Invalid type for ownerProviderId field'),
        ('missing_product_class', MISSING_CLASS, None, ValueError, 'Missing a required field in model info: productClass'),
        ('invalid_product_class_type', INV_CLASS, None, TypeError, 'Invalid type for productClass field')
    ])
    def test_create_model(self, name, data, exp_data, err_type=None, err_msg=None):

        error = None
        try:
            self.manager.create_revenue_model(deepcopy(data))
        except Exception as e:
            error = e

        if err_type is None:
            self.assertTrue(error is None)
            self.manager._make_request.assert_called_once_with('POST', 'http://testhost.com/rssHost/rss/models', exp_data)
        else:
            self.assertTrue(isinstance(e, err_type))
            self.assertEquals(err_msg, unicode(e))

    def test_update_model(self):
        self.manager.update_revenue_model(deepcopy(BASIC_MODEL))
        self.manager._make_request.assert_called_once_with('PUT', 'http://testhost.com/rssHost/rss/models', EXP_BASIC_MODEL)
