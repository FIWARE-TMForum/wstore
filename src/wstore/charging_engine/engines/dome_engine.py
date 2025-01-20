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

from django.conf import settings


class DomeEngine:
    def __init__(self, order):
        self._order = order

    def end_charging(self, transactions, free_contracts, concept):
        pass

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
        url = settings.DOME_BILLING_URL + "/price/order"
        
        data = {
            "productOrderItem": [self._build_item(contract) for contract in self._order.contracts],
            "relatedParty": [{
                'id': party['id'],
                'href': party['href'],
                'role': party['role'],
                '@referredType': 'organization'
            } for party in raw_order["relatedParty"]],
            "billingAccount": raw_order["billingAccount"]
        }

        resp = requests.post(url, json=data)
        resp.raise_for_status()

        # TODO: Integrate the payment process
        response = resp.json()
        prices = response["orderTotalPrice"]

        # Only one time and recurring-prepaid models need to be paid now
        return None
