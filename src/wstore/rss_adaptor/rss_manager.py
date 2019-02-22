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



import requests

from django.conf import settings


class RSSManager(object):

    _rss = None
    _credentials = None

    def __init__(self, credentials):
        self._credentials = credentials

    def _make_request(self, method, url, data={}):
        """
           Makes requests to the RSS
        """

        roles = ''

        for role in self._credentials['roles']:
            roles += role + ','

        headers = {
            'content-type': 'application/json',
            'X-Nick-Name': self._credentials['user'],
            'X-Roles': roles[:-1],
            'X-Email': self._credentials['email']
        }

        methods = {
            'POST': requests.post,
            'PUT': requests.put
        }

        response = methods[method](url, json=data, headers=headers)
        response.raise_for_status()

        return response

    def set_credentials(self, credentials):
        self._credentials = credentials


class ProviderManager(RSSManager):

    def register_aggregator(self, aggregator_info):
        """
        register a new aggregator in the RSS
        """
        endpoint = settings.RSS + '/rss/aggregators'
        self._make_request('POST', endpoint, aggregator_info)

    def register_provider(self, provider_info):
        """
        Register a new provider in the RSS v2
        """

        endpoint = settings.RSS + '/rss/providers'
        self._make_request('POST', endpoint, provider_info)
