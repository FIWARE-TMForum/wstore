from threading import Thread
from wstore.rss.models import RSSModel, CDR, SettlementReport
from decimal import Decimal
from wstore.rss.algorithms.rss_algorithm import RSS_ALGORITHMS
from datetime import datetime as dt


class SettlementThread(Thread):
    def __init__(self, providerId, productClass):
        super().__init__()
        self.providerId = providerId
        self.productClass = productClass

    def run(self):
        model = RSSModel.objects.get(providerId=self.providerId, productClass=self.productClass)
        transactions = (
            CDR.objects.select_for_update()
            .filter(providerId=self.providerId, productClass=self.productClass)
            .exclude(state=CDR.TransactionStates.SETTLED)
        )

        if not transactions:
            return 0

        transactions.update(state=CDR.TransactionStates.PROCESSING)
        currency = transactions[0].currency
        value = Decimal("0")
        for cdr in transactions:
            if cdr.transactionType == CDR.TransactionTypes.CHARGE:
                value += cdr.chargedAmount
            else:
                value -= cdr.chargedAmount

        algorithm = RSS_ALGORITHMS[model.algorithmType]
        revenue_share = algorithm.calculate_revenue_share(model, value)

        SettlementReport(
            **{k: v for k, v in revenue_share.items() if k in SettlementReport.field_names()},
            timestamp=dt.now(),
            currency=currency,
        ).save()

        return transactions.update(state=CDR.TransactionStates.SETTLED)
