# -*- encoding: utf-8 -*-

# Copyright (c) 2023 ficodes

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


import os

# import random
# import string

import stripe
from django.conf import settings
from logging import getLogger
from decimal import Decimal

from wstore.charging_engine.payment_client.payment_client import PaymentClient, PaymentClientError
from wstore.ordering.models import Offering


logger = getLogger("wstore.default_logger")

MODE = "sandbox"  # sandbox or live

stripe.api_key = os.environ.get(
    "BAE_CB_STRIPE_API_KEY", "sk_test_CGGvfNiIPwLXiDwaOfZ3oX6Y"  # PUBLIC SAMPLE API KEY DO NOT USE!!!
)


class StripeClient(PaymentClient):
    NAME = "stripe"
    END_PAYMENT_PARAMS = ("session_id",)

    _purchase = None
    _checkout_url = None

    def __init__(self, order):
        """Creates a new Stripe Payment Client

        Args:
            order (ordering.models.Order): the order to pay.
        """
        self._order = order

    def start_redirection_payment(self, transactions):
        """Start the payment process and produces a url to the stripe payment gateway.

        Args:
            transactions (list): a list of the transactions to bundle in a payment
        """
        logger.debug(f"Starting redirection payment to Stripe for order {self._order}")

        # Build URL
        url = settings.SITE
        if url[-1] != "/":
            url += "/"

        url += "payment?client=stripe&session_id={CHECKOUT_SESSION_ID}"
        return_url = url + "&action=accept&ref=" + str(self._order.pk)
        cancel_url = url + "&action=cancel&ref=" + str(self._order.pk)

        if not self._order.owner_organization.private:
            # The request has been made on behalf an organization
            return_url += "&organization=" + self._order.owner_organization.name
            cancel_url += "&organization=" + self._order.owner_organization.name

        products = {contract.item_id: Offering.objects.get(_id=contract.offering) for contract in self._order.contracts}

        # Build payment object
        try:
            logger.debug(f"Creating checkout session for order {self._order.order_id}")
            checkout = stripe.checkout.Session.create(
                success_url=return_url,
                cancel_url=cancel_url,
                client_reference_id=str(self._order.pk),
                mode="payment",
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": t["currency"],
                            "unit_amount": int(Decimal(t["price"]) * Decimal(100)),
                            "product_data": {
                                "name": products[t["item"]].name,
                                "description": products[t["item"]].description
                                if products[t["item"]].description
                                else "No description",
                            },
                        },
                    }
                    for t in transactions
                ],
            )

        # Check for errors in session
        except Exception as e:  # TODO: Narrow exceptions caught
            logger.error(e)
            raise PaymentClientError(self.NAME, "The checkout session cannot be created.") from e

        # Extract URL where redirecting the customer
        self._order._sales_id = [checkout.id]
        self._order.save()
        self._checkout_url = checkout.url
        return checkout.url

    def direct_payment(self, currency, price, credit_card):
        pass

    def end_redirection_payment(self, **kwargs):
        """Finalizes the payment process

        Keyword Args:
            session_id: The checkout session id
        """
        logger.debug(f"Stripe payment for order {self._order.order_id} completed")
        return [kwargs["session_id"]]

    def refund(self, session_id):
        try:
            checkout = stripe.checkout.Session.retrieve(session_id)
            refund = stripe.Refund.create(payment_intent=checkout.payment_intent)
            logger.debug(f"Refunding Stripe payment for checkout {session_id}")
            return refund

        except Exception as e:
            logger.error(f"Couldn't refund Stripe payment for checkout {session_id}")
            raise PaymentClientError(self.NAME, "The refund cannot be completed") from e

    def get_checkout_url(self):
        return self._checkout_url

    def batch_payout(self, payouts):
        # TODO: Translate to Stripe API.
        pass
        # sender_batch_id = "".join(random.choice(string.ascii_uppercase) for i in range(12))
        # payout = paypalrestsdk.Payout(
        #     {
        #         "sender_batch_header": {
        #             "sender_batch_id": sender_batch_id,
        #             "email_subject": "You have a payment",
        #         },
        #         "items": payouts,
        #     }
        # )
        #
        # return payout, payout.create()
