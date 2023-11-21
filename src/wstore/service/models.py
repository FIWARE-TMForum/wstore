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

from djongo import models

class Service(models.Model):
    _id = models.ObjectIdField()
    uuid = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)
    startDate = models.DateTimeField()
    party_id = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    characteristics = models.JSONField()

    def serialize(self):
        return {
            "id": self.uuid,
            "href": self.uuid,
            "name": self.name,
            "description": self.description,
            "startDate": str(self.startDate),
            "state": self.state,
            "relatedParty": [{
                "id": self.party_id,
                "href": self.party_id,
                "role": "Customer"
            }],
            "serviceCharacteristic": [{
                "name": charact["name"],
                "valueType": "string",
                "value": charact["value"]
            } for charact in self.characteristics]
        }
