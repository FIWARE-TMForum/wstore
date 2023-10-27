from wstore.rss import cdr_manager
from wstore.rss.models import CDR
from mock import MagicMock
from django.test import TestCase
from parameterized import parameterized
from decimal import Decimal
from bson import ObjectId

INITIAL_EXP = [
    {
        "providerId": "provider",
        "correlationNumber": "1",
        "referenceCode": "1 3",
        "application": "4 offering 1.0",
        "productClass": "one time",
        "description": "One time payment: 12 EUR",
        "currency": "EUR",
        "chargedAmount": Decimal("12"),
        "chargedTaxAmount": Decimal("2"),
        "customerId": "customer",
        "event": "One time payment event",
        "timestamp": "2015-10-21 06:13:26.661650",
        "transactionType": CDR.TransactionTypes.CHARGE,
    }
]

RECURRING_EXP = [
    {
        "providerId": "provider",
        "correlationNumber": "1",
        "referenceCode": "1 3",
        "application": "4 offering 1.0",
        "productClass": "one time",
        "description": "Recurring payment: 12 EUR monthly",
        "currency": "EUR",
        "chargedAmount": Decimal("12"),
        "chargedTaxAmount": Decimal("2"),
        "customerId": "customer",
        "event": "Recurring payment event",
        "timestamp": "2015-10-21 06:13:26.661650",
        "transactionType": CDR.TransactionTypes.CHARGE,
    }
]

USAGE_EXP = [
    {
        "providerId": "provider",
        "correlationNumber": "1",
        "referenceCode": "1 3",
        "application": "4 offering 1.0",
        "productClass": "one time",
        "description": "Fee per invocation, Consumption: 25",
        "currency": "EUR",
        "chargedAmount": Decimal("25.0"),
        "chargedTaxAmount": Decimal("5.0"),
        "customerId": "customer",
        "event": "Pay per use event",
        "timestamp": "2015-10-21 06:13:26.661650",
        "transactionType": CDR.TransactionTypes.CHARGE,
    }
]


class CDRGenerationTestCase(TestCase):
    tags = ("cdr",)

    def setUp(self):
        # Create Mocks
        cdr_manager.CDRRegistrationThread = MagicMock()

        self._conn = MagicMock()
        cdr_manager.get_database_connection = MagicMock()
        cdr_manager.get_database_connection.return_value = self._conn

        self._conn.wstore_organization.find_and_modify.side_effect = [
            {"correlation_number": 1},
            {"correlation_number": 2},
        ]

        self._order = MagicMock()
        self._order.order_id = "1"
        self._order.owner_organization.name = "customer"

        self._contract = MagicMock()
        self._contract.revenue_class = "one time"
        self._contract.offering = "61004aba5e05acc115f022f0"
        self._contract.item_id = "3"
        self._contract.pricing_model = {"general_currency": "EUR"}

        offering = MagicMock()
        offering.pk = "61004aba5e05acc115f022f0"
        offering.off_id = "4"
        offering.name = "offering"
        offering.version = "1.0"
        offering.owner_organization.name = "provider"
        offering.owner_organization.pk = "61004aba5e05acc115f022f0"

        cdr_manager.Offering = MagicMock()
        cdr_manager.Offering.objects.get.return_value = offering

    @parameterized.expand(
        [
            (
                "initial_charge",
                {
                    "single_payment": [
                        {
                            "value": Decimal("12"),
                            "unit": "one time",
                            "tax_rate": Decimal("20"),
                            "duty_free": Decimal("10"),
                        }
                    ]
                },
                INITIAL_EXP,
            ),
            (
                "recurring_charge",
                {
                    "subscription": [
                        {
                            "value": Decimal("12"),
                            "unit": "monthly",
                            "tax_rate": Decimal("20"),
                            "duty_free": Decimal("10"),
                        }
                    ]
                },
                RECURRING_EXP,
            ),
            (
                "usage",
                {
                    "accounting": [
                        {
                            "accounting": [
                                {
                                    "order_id": "1",
                                    "product_id": "1",
                                    "customer": "customer",
                                    "value": "15",
                                    "unit": "invocation",
                                },
                                {
                                    "order_id": "1",
                                    "product_id": "1",
                                    "customer": "customer",
                                    "value": "10",
                                    "unit": "invocation",
                                },
                            ],
                            "model": {
                                "unit": "invocation",
                                "currency": "EUR",
                                "value": "1",
                            },
                            "price": Decimal("25.0"),
                            "duty_free": Decimal("20.0"),
                        }
                    ]
                },
                USAGE_EXP,
            ),
        ]
    )
    def test_cdr_generation(self, name, applied_parts, exp_cdrs):
        cdr_m = cdr_manager.CDRManager(self._order, self._contract)
        cdr_m.generate_cdr(applied_parts, "2015-10-21 06:13:26.661650")

        # Validate calls
        self._conn.wstore_organization.find_and_modify.assert_called_once_with(
            query={"_id": "61004aba5e05acc115f022f0"},
            update={"$inc": {"correlation_number": 1}},
        )

        cdr_manager.CDRRegistrationThread.assert_called_once_with(exp_cdrs)
        cdr_manager.CDRRegistrationThread().start.assert_called_once()

        cdr_manager.Offering.objects.get.assert_called_once_with(pk=ObjectId("61004aba5e05acc115f022f0"))

    def test_refund_cdr_generation(self):
        exp_cdr = [
            {
                "providerId": "provider",
                "correlationNumber": "1",
                "referenceCode": "1 3",
                "application": "4 offering 1.0",
                "productClass": "one time",
                "description": "Refund event: 10 EUR",
                "currency": "EUR",
                "chargedAmount": Decimal("10"),
                "chargedTaxAmount": Decimal("2"),
                "customerId": "customer",
                "event": "Refund event",
                "timestamp": "2015-10-21 06:13:26.661650",
                "transactionType": CDR.TransactionTypes.REFUND,
            }
        ]

        cdr_m = cdr_manager.CDRManager(self._order, self._contract)
        cdr_m.refund_cdrs(Decimal("10"), Decimal("8"), "2015-10-21 06:13:26.661650")

        # Validate calls
        self._conn.wstore_organization.find_and_modify.assert_called_once_with(
            query={"_id": "61004aba5e05acc115f022f0"},
            update={"$inc": {"correlation_number": 1}},
        )

        cdr_manager.CDRRegistrationThread.assert_called_once_with(exp_cdr)
        cdr_manager.CDRRegistrationThread().start.assert_called_once()
