# -*- coding: utf-8 -*-

# Copyright (c) 2016 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class InventoryClient:
    def __init__(self):
        self._inventory_api = settings.INVENTORY

    def _build_callback_url(self):
        # Use the local site for registering the callback
        site = settings.LOCAL_SITE

        return urljoin(site, "charging/api/orderManagement/products")

    def get_hubs(self):
        r = requests.get(self._inventory_api + "/hub")
        r.raise_for_status()
        return r.json()

    def create_inventory_subscription(self):
        """
        Creates a subscription to the inventory API so the server will be able to activate products
        """

        callback_url = self._build_callback_url()

        for hub in self.get_hubs():
            if hub["callback"] == callback_url:
                break
        else:
            callback = {"callback": callback_url}

            r = requests.post(self._inventory_api + "/hub", json=callback)

            if r.status_code != 201 and r.status_code != 409:
                msg = "It hasn't been possible to create inventory subscription, "
                msg += "please check that the inventory API is correctly configured "
                msg += "and that the inventory API is up and running"
                raise ImproperlyConfigured(msg)

    def get_product(self, product_id):
        url = self._inventory_api + "/product/" + str(product_id)

        r = requests.get(url)
        r.raise_for_status()

        return r.json()

    def get_products(self, query={}):
        """
        Retrieves a set of products that can be filtered providing a query dict
        :param query: Dict containing the query used to filter the products
        :return: List of resulting products
        """

        qs = "?"
        for k, v in query.items():
            qs += "{}={}&".format(k, v)

        url = self._inventory_api + "/product" + qs[:-1]

        r = requests.get(url)
        r.raise_for_status()

        return r.json()

    def patch_product(self, product_id, patch_body):
        """
        Patch a given product according to the provided patch values
        :param product_id: Id if the product to be patched
        :param patch_body: New values for the product fields to be patched
        """
        # Build product url
        url = self._inventory_api + "/product/" + str(product_id)

        r = requests.patch(url, json=patch_body)
        r.raise_for_status()

        return r.json()

    def activate_product(self, product_id):
        """
        Activates a given product by changing its state to Active and providing a startDate
        :param product_id: Id of the product to be activated
        """
        patch_body = {
            "status": "Active",
            "startDate": datetime.utcnow().isoformat() + "Z",
        }
        self.patch_product(product_id, patch_body)

    def suspend_product(self, product_id):
        """
        Suspends a given product by changing its state to Suspended
        :param product_id: Id of the product to be suspended
        """
        patch_body = {"status": "Suspended"}
        self.patch_product(product_id, patch_body)

    def terminate_product(self, product_id):
        """
        terminates a given product by changing its state to Terminated
        :param product_id: Id of the product to be terminated
        """

        # Activate the product since it must be in active state to be terminated
        try:
            self.activate_product(product_id)
        except:
            pass

        patch_body = {
            "status": "Terminated",
            "terminationDate": datetime.utcnow().isoformat() + "Z",
        }
        self.patch_product(product_id, patch_body)
