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

import mock
from mock import MagicMock

from django.test import TestCase

from wstore.charging_engine.payment_client import paypal_client


class PaypalTestCase(TestCase):

    tags = ('payment-client', 'payment-client-paypal')

    def setUp(self):
        paypal_client.paypalrestsdk = MagicMock()

    def test_paypal(self):
        paypal = paypal_client.PayPalClient(None)
        paypal.batch_payout(['item1', 'item2'])
        paypal_client.paypalrestsdk.Payout.assert_called_once_with({
            'sender_batch_header': {
                'sender_batch_id': mock.ANY,
                'email_subject': "You have a payment"
            },
            'items': ['item1', 'item2']
        })

        paypal_client.paypalrestsdk.Payout().create.assert_called_once_with()
