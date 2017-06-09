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

import json
import importlib
from bson import ObjectId

from django.conf import settings
from wstore.charging_engine.charging.cdr_manager import CDRManager

from wstore.ordering.inventory_client import InventoryClient
from wstore.ordering.ordering_client import OrderingClient
from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import build_response, supported_request_mime_types, authentication_required
from wstore.ordering.models import Order
from wstore.ordering.errors import PaymentError
from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.store_commons.database import get_database_connection
from wstore.asset_manager.resource_plugins.decorators import on_product_acquired


class PayPalConfirmation(Resource):

    def _set_initial_states(self, transactions, raw_order, order):
        # Set all order items as in progress
        self.ordering_client.update_state(raw_order, 'InProgress')

        # Set order items of digital products as completed
        involved_items = [t['item'] for t in transactions]

        digital_items = [item for item in raw_order['orderItem'] if item['id'] in involved_items and
                         order.get_item_contract(item['id']).offering.is_digital]

        # Oder Items state is not checked
        # self.ordering_client.update_items_state(raw_order, 'InProgress', digital_items)
        self.ordering_client.update_items_state(raw_order, 'Completed', digital_items)

    def _set_renovation_states(self, transactions, raw_order, order):
        inventory_client = InventoryClient()

        for transaction in transactions:
            try:
                contract = order.get_item_contract(transaction['item'])
                inventory_client.activate_product(contract.product_id)

                # Activate the product
                on_product_acquired(order, contract)
            except:
                pass

    # This method is used to receive the PayPal confirmation
    # when the customer is paying using his PayPal account
    @supported_request_mime_types(('application/json',))
    @authentication_required
    def create(self, request):

        order = None
        concept = None
        self.ordering_client = OrderingClient()
        try:
            # Extract payment information
            data = json.loads(request.body)

            if 'reference' not in data or 'paymentId' not in data or 'payerId' not in data:
                raise ValueError('Missing required field. It must contain reference, paymentId, and payerId')

            reference = data['reference']
            token = data['paymentId']
            payer_id = data['payerId']

            if not Order.objects.filter(pk=reference):
                raise ValueError('The provided reference does not identify a valid order')

            db = get_database_connection()

            # Uses an atomic operation to get and set the _lock value in the purchase
            # document
            pre_value = db.wstore_order.find_one_and_update(
                {'_id': ObjectId(reference)},
                {'$set': {'_lock': True}}
            )

            # If the value of _lock before setting it to true was true, means
            # that the time out function has acquired it previously so the
            # view ends
            if not pre_value or '_lock' in pre_value and pre_value['_lock']:
                raise PaymentError('The timeout set to process the payment has finished')

            order = Order.objects.get(pk=reference)
            raw_order = self.ordering_client.get_order(order.order_id)
            pending_info = order.pending_payment
            concept = pending_info['concept']

            # If the order state value is different from pending means that
            # the timeout function has completely ended before acquiring the resource
            # so _lock is set to false and the view ends
            if pre_value['state'] != 'pending':
                db.wstore_order.find_one_and_update(
                    {'_id': ObjectId(reference)},
                    {'$set': {'_lock': False}}
                )
                raise PaymentError('The timeout set to process the payment has finished')

            # Check that the request user is authorized to end the payment
            if request.user.userprofile.current_organization != order.owner_organization or request.user != order.customer:
                raise PaymentError('You are not authorized to execute the payment')

            transactions = pending_info['transactions']

            # Get the payment client
            # Load payment client
            cln_str = settings.PAYMENT_CLIENT
            client_package, client_class = cln_str.rsplit('.', 1)

            payment_client = getattr(importlib.import_module(client_package), client_class)

            # build the payment client
            client = payment_client(order)
            order.sales_ids = client.end_redirection_payment(token, payer_id)
            order.save()

            charging_engine = ChargingEngine(order)
            charging_engine.end_charging(transactions, pending_info['free_contracts'], concept)

        except Exception as e:

            # Rollback the purchase if existing
            if order is not None and raw_order is not None:
                if concept == 'initial':
                    # Set the order to failed in the ordering API
                    # Set all items as Failed, mark the whole order as failed
                    self.ordering_client.update_items_state(raw_order, 'Failed')
                    order.delete()
                else:
                    order.state = 'paid'
                    order.pending_payment = {}
                    order.save()

            expl = ' due to an unexpected error'
            err_code = 500
            if isinstance(e, PaymentError) or isinstance(e, ValueError):
                expl = ': ' + unicode(e)
                err_code = 403

            msg = 'The payment has been canceled' + expl
            return build_response(request, err_code, msg)

        # Change states of TMForum resources (orderItems, products, etc)
        # depending on the concept of the payment

        states_processors = {
            'initial': self._set_initial_states,
            'recurring': self._set_renovation_states,
            'usage': self._set_renovation_states
        }
        states_processors[concept](transactions, raw_order, order)

        # _lock is set to false
        db.wstore_order.find_one_and_update(
            {'_id': ObjectId(reference)},
            {'$set': {'_lock': False}}
        )

        return build_response(request, 200, 'Ok')


class PayPalCancellation(Resource):

    # This method is used when the user cancel a charge
    # when is using a PayPal account
    @supported_request_mime_types(('application/json', ))
    @authentication_required
    def create(self, request):
        # In case the user cancels the payment is necessary to update
        # the database in order to avoid an inconsistent state
        try:
            data = json.loads(request.body)
            order = Order.objects.get(pk=data['reference'])

            client = OrderingClient()
            raw_order = client.get_order(order.order_id)

            # Set the order to failed in the ordering API
            # Set all items as Failed, mark the whole order as Failed
            # client.update_state(raw_order, 'Failed')
            client.update_items_state(raw_order, 'Failed')

            order.delete()
        except:
            return build_response(request, 400, 'Invalid request')

        return build_response(request, 200, 'Ok')


class PayPalRefund(Resource):

    # This method is used when the user cancel a charge
    # when is using a PayPal account
    @supported_request_mime_types(('application/json', ))
    @authentication_required
    def create(self, request):
        # In case the user cancels the payment is necessary to update
        # the database in order to avoid an inconsistent state
        try:
            data = json.loads(request.body)
            order = Order.objects.get(order_id=data['orderId'])

            # Get the payment client
            # Load payment client
            cln_str = settings.PAYMENT_CLIENT
            client_package, client_class = cln_str.rsplit('.', 1)

            payment_client = getattr(importlib.import_module(client_package), client_class)

            # build the payment client
            client = payment_client(order)

            for sale in order.sales_ids:
                client.refund(sale)

            # Only those orders with all its order items in ack state can be refunded
            # that means that all the contracts have been refunded
            for contract in order.contracts:
                if len(contract.charges) > 0:
                    cdr_manager = CDRManager(order, contract)
                    charge = contract.charges[-1]

                    # Create a refund CDR for each contract
                    cdr_manager.refund_cdrs(charge['cost'], charge['duty_free'], charge['date'].isoformat() + 'Z')

            order.delete()
        except:
            return build_response(request, 400, 'Sales cannot be refunded')

        return build_response(request, 200, 'Ok')
