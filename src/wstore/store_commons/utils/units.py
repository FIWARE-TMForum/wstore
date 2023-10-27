# -*- coding: utf-8 -*-

# Copyright (c) 2016 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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


class ChargePeriod:
    @staticmethod
    def contains(title):
        return title.lower() in settings.CHARGE_PERIODS

    @staticmethod
    def get_value(title):
        return settings.CHARGE_PERIODS.get(title.lower())

    @staticmethod
    def to_json():
        return [{"title": t, "value": v} for t, v in settings.CHARGE_PERIODS.items()]


class CurrencyCode:
    @staticmethod
    def contains(value):
        return value.upper() in [v for v, t in settings.CURRENCY_CODES]

    @staticmethod
    def to_json():
        return [{"title": t, "value": v} for v, t in settings.CURRENCY_CODES]
