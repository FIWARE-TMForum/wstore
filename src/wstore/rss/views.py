from wstore.store_commons.resource import Resource as APIResource
import json
from wstore.store_commons.utils.http import authentication_required, build_response, supported_request_mime_types
from django.core.exceptions import ValidationError
from logging import getLogger
from wstore.rss.models import RSSModel, CDR
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from wstore.rss.algorithms.rss_algorithm import RSS_ALGORITHMS

logger = getLogger("wstore.default_logger")


class RevenueSharingModels(APIResource):
    @supported_request_mime_types(("application/json",))
    @authentication_required
    def create(self, request):
        try:
            data = json.loads(request.body)
            model = RSSModel(**data)
            model.save()
            return HttpResponse(
                json.dumps(
                    model_to_dict(
                        model,
                        fields=[
                            "providerId",
                            "productClass",
                            "algorithmType",
                            "ownerValue",
                            "aggregatorValue",
                            "stakeholders",
                        ],
                    ),
                    cls=DjangoJSONEncoder,
                ),
                status=201,
                content_type="application/json; charset=utf-8",
            )

        except ValidationError as e:
            logger.error(f"Could't create Revenue Sharing Model:\n{e}")
            error = 400, f"Bad request: {e}"

        return build_response(request, *error)

    @supported_request_mime_types(("application/json",))
    @authentication_required
    def update(self, request):
        try:
            data = json.loads(request.body)
            model = RSSModel.objects.get(providerId=data["providerId"], productClass=data["productClass"])
            model.algorithmType = data.get("algorithmType", model.algorithmType)
            model.ownerValue = data.get("ownerValue", model.ownerValue)
            model.aggregatorValue = data.get("aggregatorValue", model.aggregatorValue)
            model.stakeholders = data.get("stakeholders", model.stakeholders)

            model.save(update_fields=data.keys())
            return HttpResponse(
                json.dumps(
                    model_to_dict(
                        model,
                        fields=[
                            "providerId",
                            "productClass",
                            "algorithmType",
                            "ownerValue",
                            "aggregatorValue",
                            "stakeholders",
                        ],
                    ),
                    cls=DjangoJSONEncoder,
                ),
                status=200,
                content_type="application/json; charset=utf-8",
            )

        except (NameError, KeyError) as e:
            logger.error(f"Bad request: Must contain {e}")
            error = 400, "Bad request: must contain fields `providerId`, `productClass`."
        except ValidationError as e:
            logger.error(f"Could't update Revenue Sharing Model:\n{e}")
            error = 400, f"Bad request: {e}"
        except ObjectDoesNotExist as e:
            logger.error(f"Revenue Sharing Model does not exist\n{e}")
            error = 404, "Revenue Sharing Model does not exist"

        return build_response(request, *error)

    @authentication_required
    def read(self, request):
        try:
            query_offset = int(request.GET.get("offset", 0))
            query_end = query_offset + int(request.GET.get("size", 10))
            models = list(
                RSSModel.objects.filter(
                    **{
                        param: request.GET[param]
                        for param in ("productClass", "algorithmType", "providerId")
                        if param in request.GET
                    }
                )[query_offset:query_end].values()
            )
            return HttpResponse(
                json.dumps(models, cls=DjangoJSONEncoder),
                status=200,
                content_type="application/json; charset=utf-8",
            )

        except Exception as e:
            logger.error(f"Couldn't return RSS models: \n{e}")
            error = 400, "Bad request"

        return build_response(request, *error)


class RevenueSharingAlgorithms(APIResource):
    @authentication_required
    def read(self, request):
        algorithms = [cls.to_dict() for id, cls in RSS_ALGORITHMS.items()]

        return HttpResponse(
            json.dumps(algorithms, cls=DjangoJSONEncoder), status=200, content_type="application/json; charset=utf-8"
        )


class Settlements(APIResource):
    @supported_request_mime_types(("application/json",))
    @authentication_required
    def create(self, request):
        ...
        # PSEUDO CODE
        # IN SEPARATE THREAD
        # providers = getProviders()
        # for provider in providers:
        #     for model in provider.getModels():
        #         transactions = getTransactions(Model)
        #         if transactions:
        #             setTransactionsState(transactions, "processing")
        #             runTask(settlementTask, transactions)


class SettlementReports(APIResource):
    ...


class CDRs(APIResource):
    def read(self, request):
        try:
            query_offset = int(request.GET.get("offset", 0))
            query_end = query_offset + int(request.GET.get("size", 10))
            models = list(
                CDR.objects.filter(**{param: request.GET[param] for param in ("providerId") if param in request.GET})[
                    query_offset:query_end
                ].values()
            )
            return HttpResponse(
                json.dumps(models, cls=DjangoJSONEncoder),
                status=200,
                content_type="application/json; charset=utf-8",
            )

        except Exception as e:
            logger.error(f"Couldn't return RSS models: \n{e}")
            error = 400, "Bad request"

        return build_response(request, *error)
