# -*- coding: utf-8 -*-

# Copyright (c) 2024 Future Internet Consulting and Development Solutions S.L.

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

import requests
import json

from django.conf import settings
from logging import getLogger

from wstore.charging_engine.charging.billing_client import BillingClient
from wstore.ordering.inventory_client import InventoryClient

logger = getLogger("wstore.default_logger")


class DomeEngine:
    def __init__(self, order):
        self._order = order

    def end_charging(self, transactions, free_contracts, concept):
        # set the order as paid
        # Update renovation dates
        # Update applied customer billing rates
        pass

    def _get_item(self, item_id, raw_order):
        items = [item for item in raw_order["productOrderItem"] if item["id"] == item_id]

        return items[0] if items else None

    def _build_item(self, contract):
        return {
            "id": contract.item_id,
            "action": "add",
            "quantity": 1,
            "itemTotalPrice": [{
                "productOfferingPrice": contract.pricing_model
            }],
            "productOffering": {
                "id": contract.offering,
                "href": contract.offering
            },
            "product": {
                "productCharacteristic": contract.options
            }
        }

    def resolve_charging(self, type_="initial", related_contracts=None, raw_order=None):
        # Use the dome billing engine to resolve the charging
        url = settings.DOME_BILLING_URL + "/billing/instantBill"

        # The billing engine processes the products one by one
        inventory = InventoryClient()

        # TODO: Potentially another filter needs to be included as
        # recurring postpaid and usage models are not paid now
        new_contracts = []
        billing_client = BillingClient()
        for contract in self._order.contracts:
            data = inventory.build_product_model(
                    self._get_item(contract.item_id, raw_order), raw_order["id"], raw_order["billingAccount"])

            logger.info("Calling the billing engine with " + json.dumps(data))

            resp = requests.post(url, json=data)
            resp.raise_for_status()

            response = resp.json()

            logger.info("Received response " + json.dumps(response))

            # Create the Billing rates as not billed
            inv_ids = billing_client.create_batch_customer_rates(response)

            contract.applied_rates = inv_ids
            new_contracts.append(contract)

        # Update the order with the new contracts
        self._order.contracts = new_contracts
        self._order.save()

        # TODO: Check the local charging for info on the db objects that needs to be created for the payment

        # Call the payment gateway
        # Return the redirect URL to process the payment

        logger.info("Billing processed")
        return None
