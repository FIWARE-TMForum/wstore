# -*- coding: utf-8 -*-

# Copyright (c) 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from wstore.asset_manager.inventory_upgrader import InventoryUpgrader
from wstore.asset_manager.models import Resource
from wstore.models import Context
from wstore.store_commons.database import DocumentLock


class Command(BaseCommand):
    def handle(self, *args, **kargs):

        contexts = Context.objects.all()

        if len(contexts) < 1:
            raise CommandError('Context object is not yet created')

        context_id = contexts[0].pk

        # Context object is locked in order to avoid possible inconsistencies
        # in the list of pending upgrade notifications
        lock = DocumentLock('wstore_context', context_id, 'ctx')
        lock.wait_document()

        context = Context.objects.get(pk=context_id)

        # Get pending product notifications and resend them
        pending_upgrades = context.failed_upgrades

        failed_upgrades = []
        for upgrade in pending_upgrades:
            asset = Resource.objects.get(pk=upgrade['asset_id'])
            upgrader = InventoryUpgrader(asset)

            # Check if there is a list of products or if it is needed to upgrade all
            missing_products = []
            missing_off = []
            if len(upgrade['pending_products']) > 0:
                missing_products.extend(upgrader.upgrade_products(upgrade['pending_products'], lambda p_id: p_id))

            if len(upgrade['pending_offerings']) > 0:
                missing_off, partial_prods = upgrader.upgrade_asset_products(upgrade['pending_offerings'])
                missing_products.extend(partial_prods)

            if len(missing_products) > 0 or len(missing_off) > 0:
                failed_upgrades.append({
                    'asset_id': asset.pk,
                    'pending_offerings': missing_off,
                    'pending_products': missing_products
                })

        context.failed_upgrades = failed_upgrades
        context.save()

        # Release Context object
        lock.unlock_document()
