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



import requests

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **kargs):
        headers = {
            'content-type': 'application/json',
            'X-Nick-Name': settings.STORE_NAME,
            'X-Roles': settings.ADMIN_ROLE,
            'X-Email': settings.WSTOREMAIL
        }

        local_site = settings.LOCAL_SITE
        url = '{}/charging/api/reportManagement/created'.format(local_site)
        data = {"aggregatorId": None, "providerId": None, "productClass": None, "callbackUrl": url}

        # Make request
        url = settings.RSS
        if not url.endswith('/'):
            url += '/'

        url += 'rss/settlement'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 202:
            print(("Some error asking to generate reports:\n{}: {}".format(response.reason, response.text)))
        else:
            print("Sended.")
