import json
from copy import deepcopy
from datetime import datetime
from importlib import reload

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from parameterized import parameterized

from wstore.charging_engine.accounting import usage_client
from wstore.charging_engine.accounting.errors import UsageError

# ./manage.py test wstore.charging_engine.accounting.integration_t_usage

EMPTY_USAGE = {}

EMPTY_USAGE_SPECIFICATION = {}

PARTY_USAGE = {
    "relatedParty": [{"id": "1", "name": "string"}, {"id": "1", "name": "string"}],
}


class UsageClientTestCase(TestCase):
    tags = ("usage-client",)

    def setUp(self):
        self._old_inv = usage_client.settings.INVENTORY
        usage_client.settings.INVENTORY = "http://localhost:8080/DSProductInventory"
        usage_client.settings.USAGE = "http://host.docker.internal:8632"

        self._customer = "test_customer"
        self._product_id = "1"

    def tearDown(self):
        usage_client.settings.INVENTORY = self._old_inv

    def _addIdHref(self, gson, returned):
        print(returned["id"])

        gson["id"] = returned["id"]
        gson["href"] = returned["href"]

    @parameterized.expand([("empty usage", EMPTY_USAGE, EMPTY_USAGE)])
    def test_create_usage(self, name, response, exp_resp):
        client = usage_client.UsageClient()
        created_usage = client.create_usage(response)
        self._addIdHref(exp_resp, created_usage)
        self.assertEquals(exp_resp, created_usage)

    def _test_patch(self, expected_json, method, args):
        method(*args)

        # Verify calls
        usage_client.requests.patch.assert_called_once_with(
            usage_client.settings.USAGE + "/usage/" + BASIC_USAGE["id"],
            json=expected_json,
        )

    @parameterized.expand([("empty usage", EMPTY_USAGE, EMPTY_USAGE)])
    def test_update_usage_state(self, name, response, exp_resp):
        client = usage_client.UsageClient()
        created_usage = client.create_usage(response)

        status = "rated"
        expected_json = {"status": status}
        client.update_usage_state(created_usage["id"], status)

        # The update works, but it does not return anything so no

    @parameterized.expand([("empty usageSpecification", EMPTY_USAGE_SPECIFICATION, EMPTY_USAGE_SPECIFICATION)])
    def test_create_usageSpecification(self, name, response, exp_resp):
        client = usage_client.UsageClient()
        created_usage_specification = client.create_usage_spec(response)
        self._addIdHref(exp_resp, created_usage_specification)
        self.assertEquals(exp_resp, created_usage_specification)

    @parameterized.expand([("empty usageSpecification", EMPTY_USAGE_SPECIFICATION, EMPTY_USAGE_SPECIFICATION)])
    def test_delete_usageSpecification(self, name, response, exp_resp):
        client = usage_client.UsageClient()
        created_usage_specification = client.create_usage_spec(response)
        self._addIdHref(exp_resp, created_usage_specification)
        client.delete_usage_spec(created_usage_specification["id"])

        # Not return or retrieve on usage_client so no assert but it works
