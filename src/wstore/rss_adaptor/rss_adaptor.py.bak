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

import requests
import threading
from bson import ObjectId

from django.conf import settings

from wstore.store_commons.database import get_database_connection
from wstore.models import Context, Organization


class RSSAdaptorThread(threading.Thread):

    def __init__(self, cdr_info):
        threading.Thread.__init__(self)
        self.cdr = cdr_info

    def run(self):
        r = RSSAdaptor()
        r.send_cdr(self.cdr)


class RSSAdaptor:

    def send_cdr(self, cdr_info):
        # Build CDRs
        data = []
        for cdr in cdr_info:

            data.append({
                'cdrSource': settings.WSTOREMAIL,
                'productClass': cdr['product_class'],
                'correlationNumber': cdr['correlation'],
                'timestamp': cdr['time_stamp'],
                'application': cdr['offering'],
                'transactionType': cdr['type'],
                'event': cdr['event'],
                'referenceCode': cdr['order'],
                'description': cdr['description'],
                'chargedAmount': cdr['cost_value'],
                'chargedTaxAmount': cdr['tax_value'],
                'currency': cdr['cost_currency'],
                'customerId': cdr['customer'],
                'appProvider': cdr['provider']
            })

        # Make request
        url = settings.RSS
        if not url.endswith('/'):
            url += '/'

        url += 'rss/cdrs'

        headers = {
            'content-type': 'application/json',
            'X-Nick-Name': settings.STORE_NAME,
            'X-Roles': settings.ADMIN_ROLE,
            'X-Email': settings.WSTOREMAIL
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            db = get_database_connection()
            # Restore correlation numbers
            for cdr in cdr_info:
                org = Organization.objects.get(name=cdr['provider'])
                db.wstore_organization.find_and_modify(
                    query={'_id': ObjectId(org.pk)},
                    update={'$inc': {'correlation_number': -1}}
                )['correlation_number']

            context = Context.objects.all()[0]
            context.failed_cdrs.extend(cdr_info)
            context.save()
