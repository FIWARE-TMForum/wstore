# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid
# Copyright (c) 2021 Future Internet Consulting and Development Solutions S.L.

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

from django.conf import settings

from wstore.charging_engine.engines.local_engine import LocalEngine
from wstore.charging_engine.engines.dome_engine import DomeEngine


class ChargingEngine:

    def __init__(self, order):
        # Set billing engine to be used
        engines = {
            'local': LocalEngine,
            'dome': DomeEngine
        }

        self._billing_engine = engines[settings.BILLING_ENGINE](order)

    def end_charging(self, transactions, free_contracts, concept):
        return self._billing_engine.end_charging(transactions, free_contracts, concept)

    def resolve_charging(self, type_="initial", related_contracts=None, raw_order=None):
        return self._billing_engine.resolve_charging(
            type_, related_contracts=related_contracts, raw_order=raw_order)
