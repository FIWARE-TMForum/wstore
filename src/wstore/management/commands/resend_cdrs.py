# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid

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

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from wstore.models import Context, Organization
from wstore.rss.cdr_manager import register_cdr
from wstore.store_commons.database import get_database_connection


class Command(BaseCommand):
    def handle(self, *args, **kargs):
        """
        Launch failed cdrs
        """
        contexts = Context.objects.all()
        if len(contexts) < 1:
            raise CommandError("No context")

        context = contexts[0]
        cdrs = context.failed_cdrs
        context.failed_cdrs = []
        context.save()

        if len(cdrs) == 0:
            print("No failed cdrs to send")
            exit(0)

        db = get_database_connection()
        time_stamp = datetime.utcnow().isoformat() + "Z"

        for cdr in cdrs:
            # Modify time_stamp
            cdr["time_stamp"] = time_stamp

            # Modify correlation number
            org = Organization.objects.get(name=cdr["provider"])

            new_org = db.wstore_organization.find_and_modify(
                query={"_id": org.pk}, update={"$inc": {"correlation_number": 1}}
            )

            cdr["correlation"] = new_org["correlation_number"]

        register_cdr(cdrs)
