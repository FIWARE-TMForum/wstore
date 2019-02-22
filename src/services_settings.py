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



VERIFY_REQUESTS = True

SITE = 'http://proxy.docker:8004/'
LOCAL_SITE = 'http://charging.docker:8006/'

CATALOG = 'http://apis.docker:8080/DSProductCatalog'
INVENTORY = 'http://apis.docker:8080/DSProductInventory'
ORDERING = 'http://apis.docker:8080/DSProductOrdering'
BILLING = 'http://apis.docker:8080/DSBillingManagement'
RSS = 'http://rss.docker:8080/DSRevenueSharing'
USAGE = 'http://apis.docker:8080/DSUsageManagement'
AUTHORIZE_SERVICE = 'http://proxy.docker:8004/authorizeService/apiKeys'
