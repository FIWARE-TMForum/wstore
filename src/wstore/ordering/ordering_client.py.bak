# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid

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

import requests
from urlparse import urljoin

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class OrderingClient:

    def __init__(self):
        self._ordering_api = settings.ORDERING

    def create_ordering_subscription(self):
        """
        Create a subscription in the ordering API for being notified on product orders creation
        :return:
        """

        # Use the local site for registering the callback
        site = settings.LOCAL_SITE

        callback = {
            'callback': urljoin(site, 'charging/api/orderManagement/orders')
        }

        r = requests.post(self._ordering_api + '/productOrdering/v2/hub', callback)

        if r.status_code != 200 and r.status_code != 409:
            msg = "It hasn't been possible to create ordering subscription, "
            msg += 'please check that the ordering API is correctly configured '
            msg += 'and that the ordering API is up and running'
            raise ImproperlyConfigured(msg)

    def get_order(self, order_id):
        path = '/DSProductOrdering/api/productOrdering/v2/productOrder/' + unicode(order_id)
        url = urljoin(self._ordering_api, path)

        r = requests.get(url)
        r.raise_for_status()

        return r.json()

    def update_state(self, order, state):
        """
        Change the state of a given order including without changing the state of the items
        :param order: Order object as returned by the ordering API
        :param state: New state
        :return:
        """

        # Build patch body
        patch = {
            'state': state,
        }

        # Make PATCH request
        path = '/DSProductOrdering/api/productOrdering/v2/productOrder/' + unicode(order['id'])
        url = urljoin(self._ordering_api, path)

        r = requests.patch(url, json=patch)

        r.raise_for_status()

    def update_items_state(self, order, state, items=None):

        """
        Change the state of a given order including its order items
        :param order: Order object as returned by the ordering API
        :param items: list of order items to be updated
        :param state: New state
        :return:
        """

        # Build patch body
        patch = {
            'orderItem': [],
        }

        if items is None:
            items = order['orderItem']

        for orderItem in order['orderItem']:
            for item in items:
                if orderItem['id'] == item['id']:
                    orderItem['state'] = state

            patch['orderItem'].append(orderItem)

        # Make PATCH request
        path = '/DSProductOrdering/api/productOrdering/v2/productOrder/' + unicode(order['id'])
        url = urljoin(self._ordering_api, path)

        r = requests.patch(url, json=patch)

        r.raise_for_status()
