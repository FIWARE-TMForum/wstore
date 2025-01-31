from wstore.charging_engine.payment_client.payment_client import PaymentClient
from wstore.ordering.errors import PaymentError
from django.conf import settings

import os
import requests
from decimal import Decimal
from logging import getLogger

logger = getLogger("wstore.default_logger")

DPAS_CLIENT_API_URL = os.environ.get("BAE_CB_DPAS_CLIENT_API_URL", "https://dpas-sbx.egroup.hu/api/payment-start")

class DpasClient(PaymentClient):
    _checkout_url = None

    def __init__(self, order):
        self._order = order
        self.api_url = DPAS_CLIENT_API_URL 

    def start_redirection_payment(self, transactions):       
        total = Decimal("0")
        current_curr = transactions[0]["currency"]
        for t in transactions:
            if t["currency"] != current_curr:
                raise PaymentError("The payment cannot be created: Multiple currencies")
            total += Decimal(t["price"])

        redirect_uri = settings.SITE
        payload = {
            "externalId": str(self._order.order_id),
            "customerId": self._order.customer_id, 
            "customerOrganizationId": str(self._order.owner_organization_id),
            "type": "ONETIME", # recurring payment type is not yet implemented in the Dpas API
            "invoiceId": "invoice id", # should be the order's invoice ID
            "paymentItems": [{
                "productProviderId": "1", # should be the product provider's ID
                "amount": str(total),
                "currency": current_curr,
                "recurring" : False,
                "productProviderSpecificData": {}
            }],
            "processSuccessUrl": redirect_uri,
            "processErrorUrl": redirect_uri
        }

        try:
            response = requests.post(self.api_url, json=payload)
            self._checkout_url = response.json()["redirectUrl"]
            return self._checkout_url

        except requests.RequestException as e:
            logger.debug(f"Error contacting payment API: {e}")

    def end_redirection_payment(self, token, payer_id):
        pass

    def refund(self, sale_id):
        pass

    def get_checkout_url(self):
        return self._checkout_url