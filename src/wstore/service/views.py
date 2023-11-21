# -*- coding: utf-8 -*-

# Copyright (c) 2023 Future Internet Consulting and Development Solutions S.L.

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

import json

from django.http import HttpResponse

from wstore.service.models import Service
from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import authentication_required, build_response, supported_request_mime_types


class ServiceCollection(Resource):

    def read(self, request):

        party_id = request.GET.get("relatedParty.id", None)

        if party_id is None:
            return build_response(
                request,
                422,
                "Please specify a relatedParty id",
            )

        try:
            services = Service.objects.filter(party_id=party_id)
            response = [serv.serialize() for serv in services]
        except:
            return build_response(
                request,
                500,
                "Unpected error reading services",
            )

        return HttpResponse(
            json.dumps(response),
            status=200,
            content_type="application/json; charset=utf-8",
        )


class ServiceEntry(Resource):

    def read(self, request, service_id):
        try:
            service = Service.objects.get(uuid=service_id)
            response = service.serialize()
        except:
            return build_response(
                request,
                500,
                "Unpected error reading services",
            )

        return HttpResponse(
            json.dumps(response),
            status=200,
            content_type="application/json; charset=utf-8",
        )
