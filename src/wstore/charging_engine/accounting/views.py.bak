# -*- coding: utf-8 -*-

# Copyright (c) 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

import json

from django.core.exceptions import PermissionDenied

from wstore.charging_engine.accounting.sdr_manager import SDRManager
from wstore.charging_engine.accounting.usage_client import UsageClient
from wstore.ordering.models import Order
from wstore.asset_manager.resource_plugins.decorators import on_usage_refreshed
from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response, supported_request_mime_types


class ServiceRecordCollection(Resource):

    # This method is used to load SDR documents and
    # start the charging process
    @supported_request_mime_types(('application/json',))
    def create(self, request):
        try:
            # Extract SDR document from the HTTP request
            data = json.loads(request.body)
        except:
            # The usage document is not valid, so the state cannot be changed
            return build_response(request, 400, 'The request does not contain a valid JSON object')

        # Validate usage information
        response = None
        sdr_manager = SDRManager()
        try:
            sdr_manager.validate_sdr(data)
        except PermissionDenied as e:
            response = build_response(request, 403, unicode(e))
        except ValueError as e:
            response = build_response(request, 422, unicode(e))
        except:
            response = build_response(request, 500, 'The SDR document could not be processed due to an unexpected error')

        usage_client = UsageClient()
        if response is not None:
            # The usage document is not valid, change its state to Rejected
            usage_client.update_usage_state(data['id'], 'Rejected')
        else:
            # The usage document is valid, change its state to Guided
            usage_client.update_usage_state(data['id'], 'Guided')
            sdr_manager.update_usage()
            response = build_response(request, 200, 'OK')

        # Update usage document state
        return response


class SDRRefreshCollection(Resource):

    @supported_request_mime_types(('application/json',))
    def create(self, request):
        try:
            data = json.loads(request.body)
        except:
            return build_response(request, 400, 'The request does not contain a valid JSON object')

        if 'orderId' not in data or 'productId' not in data:
            return build_response(request, 422, 'Missing required field, it must include orderId and productId')

        # Get order and product info
        try:
            order = Order.objects.get(order_id=data['orderId'])
        except:
            return build_response(request, 404, 'The oid specified in the product name is not valid')

        try:
            contract = order.get_product_contract(data['productId'])
        except:
            return build_response(request, 404, 'The specified product id is not valid')

        # Refresh accounting information
        on_usage_refreshed(order, contract)

        return build_response(request, 200, 'Ok')
