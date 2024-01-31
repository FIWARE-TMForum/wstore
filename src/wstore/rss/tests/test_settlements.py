# from copy import deepcopy
# from importlib import reload

# from django.conf import settings
from django.test import TestCase
from mock import MagicMock, ANY
from parameterized import parameterized

# import wstore.store_commons.utils.http as http_utils
# import wstore.rss.views as rss_views
import wstore.rss.models as rss_models
import wstore.rss.settlement as rss_settlement
from decimal import Decimal

# from django.test.client import Client
# from json import dumps, loads
# from django.core.exceptions import ObjectDoesNotExist

TRANSACTIONS = [
    {  # ---------------------------------
        "productClass": "pc1",
        "correlationNumber": "0000",
        "state": "R",
        "timestamp": "2023-01-01",
        "application": "app1",
        "transactionType": "C",
        "event": "e1",
        "referenceCode": "ref0000",
        "description": "desc0000",
        "chargedAmount": Decimal("100.000"),
        "chargedTaxAmount": Decimal("21.000"),
        "currency": "EUR",
        "customerId": "c1",
        "providerId": "p1",
    },
    {  # ---------------------------------
        "productClass": "pc1",
        "correlationNumber": "0001",
        "state": "R",
        "timestamp": "2023-01-01",
        "application": "app1",
        "transactionType": "C",
        "event": "e1",
        "referenceCode": "ref0001",
        "description": "desc0001",
        "chargedAmount": Decimal("50.000"),
        "chargedTaxAmount": Decimal("10.500"),
        "currency": "EUR",
        "customerId": "c1",
        "providerId": "p1",
    },
    {  # ---------------------------------
        "productClass": "pc1",
        "correlationNumber": "0002",
        "state": "R",
        "timestamp": "2023-01-01",
        "application": "app1",
        "transactionType": "R",
        "event": "e2",
        "referenceCode": "ref0002",
        "description": "desc0002",
        "chargedAmount": Decimal("20.000"),
        "chargedTaxAmount": Decimal("4.200"),
        "currency": "EUR",
        "customerId": "c2",
        "providerId": "p1",
    },
    {  # ---------------------------------
        "productClass": "pc1",
        "correlationNumber": "0003",
        "state": "R",
        "timestamp": "2023-01-01",
        "application": "app2",
        "transactionType": "C",
        "event": "e2",
        "referenceCode": "ref0003",
        "description": "desc0003",
        "chargedAmount": Decimal("100.000"),
        "chargedTaxAmount": Decimal("21.000"),
        "currency": "EUR",
        "customerId": "c2",
        "providerId": "p1",
    },
]

MODELS = {
    "basic": {
        "providerId": "p1",
        "productClass": "pc1",
        "algorithmType": "FIXED_PERCENTAGE",
        "providerShare": Decimal("70.00"),
        "aggregatorShare": Decimal("30.00"),
    },
    "stakeholders": {
        "providerId": "p1",
        "productClass": "pc1",
        "algorithmType": "FIXED_PERCENTAGE",
        "providerShare": Decimal("50.00"),
        "aggregatorShare": Decimal("30.00"),
        "stakeholders": [
            {"stakeholderId": "st1", "stakeholderShare": Decimal("10.00")},
            {"stakeholderId": "st2", "stakeholderShare": Decimal("10.00")},
        ],
    },
}

TESTS = [
    {  # ---------------------------------
        "name": "correct_basic",
        "transactions": [TRANSACTIONS[0]],
        "model": MODELS["basic"],
        "expected": {
            "return": 1,
            "settlement": {
                "providerId": "p1",
                "productClass": "pc1",
                "algorithmType": "FIXED_PERCENTAGE",
                "currency": "EUR",
                "providerTotal": Decimal("70.0000"),
                "aggregatorTotal": Decimal("30.0000"),
                "stakeholders": [],
            },
        },
    },
    {  # ---------------------------------
        "name": "correct_no_transactions",
        "transactions": [],
        "model": MODELS["basic"],
        "expected": {"return": 0, "settlement": None},
    },
    {  # ---------------------------------
        "name": "correct_with_refunds",
        "transactions": TRANSACTIONS[:4],
        "model": MODELS["basic"],
        "expected": {
            "return": 4,
            "settlement": {
                "providerId": "p1",
                "productClass": "pc1",
                "algorithmType": "FIXED_PERCENTAGE",
                "currency": "EUR",
                "providerTotal": Decimal("161.0000"),
                "aggregatorTotal": Decimal("69.0000"),
                "stakeholders": [],
            },
        },
    },
    {  # ---------------------------------
        "name": "correct_with_stakeholders",
        "transactions": [TRANSACTIONS[0]],
        "model": MODELS["stakeholders"],
        "expected": {
            "return": 1,
            "settlement": {
                "providerId": "p1",
                "productClass": "pc1",
                "algorithmType": "FIXED_PERCENTAGE",
                "currency": "EUR",
                "providerTotal": Decimal("50.0000"),
                "aggregatorTotal": Decimal("30.0000"),
                "stakeholders": [
                    {"stakeholderId": "st1", "stakeholderTotal": Decimal("10.00")},
                    {"stakeholderId": "st2", "stakeholderTotal": Decimal("10.00")},
                ],
            },
        },
    },
]


class SettlementsTestCase(TestCase):
    tags = "rss", "rs-settlements"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        rss_models.RSSModel.objects = MagicMock()
        rss_models.CDR.objects = MagicMock()
        rss_settlement.SettlementReport = MagicMock()
        rss_settlement.SettlementReport.field_names.return_value = rss_models.SettlementReport.field_names()
        TestCase.setUp(self)

    @parameterized.expand([test.values() for test in TESTS])
    def test_launch_settlement(self, name, transactions, model, expected):
        # Setup
        rss_models.RSSModel.objects.get.return_value = rss_models.RSSModel(**model)
        mock_transactions = MagicMock(name="mock_transactions")
        mock_cdr_list = [rss_models.CDR(**t) for t in transactions]
        mock_transactions.list = mock_cdr_list
        mock_transactions.__len__.return_value = len(mock_cdr_list)
        mock_transactions.__bool__.return_value = len(mock_cdr_list) > 0
        mock_transactions.__iter__.return_value = mock_cdr_list.__iter__()
        mock_transactions.__getitem__ = lambda self, x: mock_cdr_list[x]
        mock_transactions.update.return_value = len(mock_cdr_list)

        rss_models.CDR.objects.select_for_update().filter().exclude.return_value = mock_transactions

        # Test
        settlement_thread = rss_settlement.SettlementThread(model["providerId"], model["productClass"])

        returns = settlement_thread.run()

        self.assertEquals(returns, expected["return"])
        if returns:
            self.assertEquals(len(mock_transactions.update.mock_calls), 2)
            rss_settlement.SettlementReport.assert_called_once_with(**expected["settlement"], timestamp=ANY)
