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


from datetime import datetime

from django.test import TestCase
from mock import MagicMock
from parameterized import parameterized

from wstore.charging_engine.charging import billing_client

TIMESTAMP = datetime(2016, 6, 21, 10, 0, 0)
RENEW_DATE = datetime(2016, 7, 21, 10, 0, 0)
START_DATE = datetime(2016, 5, 21, 10, 0, 0)

COMMON_CHARGE = {
    "date": TIMESTAMP.isoformat() + "Z",
    "currencyCode": "EUR",
    "taxIncludedAmount": "10",
    "taxExcludedAmount": "8",
    "appliedCustomerBillingTaxRate": [{"amount": "20", "taxCategory": "VAT"}],
    "serviceId": [{"id": "1", "type": "Inventory product"}],
}

BASIC_CHARGE = {
    "description": "initial charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf",
    "type": "initial",
}
BASIC_CHARGE.update(COMMON_CHARGE)

RECURRING_CHARGE = {
    "description": "recurring charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf",
    "type": "recurring",
    "period": [
        {
            "startPeriod": TIMESTAMP.isoformat() + "Z",
            "endPeriod": RENEW_DATE.isoformat() + "Z",
        }
    ],
}
RECURRING_CHARGE.update(COMMON_CHARGE)

USAGE_CHARGE = {
    "description": "usage charge of 10 EUR http://extpath.com:8080/charging/media/bills/bill1.pdf",
    "type": "usage",
    "period": [
        {
            "startPeriod": START_DATE.isoformat() + "Z",
            "endPeriod": TIMESTAMP.isoformat() + "Z",
        }
    ],
}
USAGE_CHARGE.update(COMMON_CHARGE)


class BillingClientTestCase(TestCase):
    tags = ("billing",)

    @parameterized.expand(
        [
            ("initial", None, None, BASIC_CHARGE),
            ("recurring", None, RENEW_DATE, RECURRING_CHARGE),
            ("usage", START_DATE, None, USAGE_CHARGE),
        ]
    )
    def test_create_charge(self, name, start_date, end_date, exp_body):
        ## TODO: This API has changed and it is not yet implemented
        pass
        # # Create Mocks
        # billing_client.settings.BILLING = "http://billing.api.com"

        # charge = {}
        # charge["date"] = TIMESTAMP
        # charge["cost"] = "10"
        # charge["duty_free"] = "8"
        # charge["invoice"] = "charging/media/bills/bill1.pdf"
        # charge["currency"] = "EUR"
        # charge["concept"] = name

        # site = "http://extpath.com:8080/"
        # billing_client.settings.SITE = site

        # billing_client.Request = MagicMock()
        # billing_client.Session = MagicMock()
        # session = MagicMock()
        # billing_client.Session.return_value = session

        # preped = MagicMock()
        # preped.headers = {}
        # session.prepare_request.return_value = preped

        # # Call the method to test
        # client = billing_client.BillingClient()
        # client.create_charge(charge, "1", start_date=start_date, end_date=end_date)

        # # Validate calls
        # billing_client.Request.assert_called_once_with(
        #     "POST",
        #     "http://billing.api.com/api/billingManagement/v2/appliedCustomerBillingCharge",
        #     json=exp_body,
        # )

        # billing_client.Session.assert_called_once_with()
        # session.prepare_request.assert_called_once_with(billing_client.Request())

        # self.assertEquals("extpath.com:8080", preped.headers["Host"])

        # session.send.assert_called_once_with(preped)
        # session.send().raise_for_status.assert_called_once_with()
