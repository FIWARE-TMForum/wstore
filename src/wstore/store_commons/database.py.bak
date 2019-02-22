# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

from bson import ObjectId
from pymongo import MongoClient

from django.conf import settings


def get_database_connection():
    """
    Gets a raw database connection to MongoDB
    """
    # Get database info from settings
    database_info = settings.DATABASES['default']

    client = None
    # Create database connection
    if database_info['HOST'] and database_info['PORT']:
        client = MongoClient(database_info['HOST'], database_info['PORT'])
    elif database_info['HOST'] and not database_info['PORT']:
        client = MongoClient(database_info['HOST'])
    elif not database_info['HOST'] and database_info['PORT']:
        client = MongoClient('localhost', database_info['PORT'])
    else:
        client = MongoClient()

    db_name = database_info['NAME']
    db = client[db_name]

    # Authenticate if needed
    if database_info['USER'] and database_info['PASSWORD']:
        db.authenticate(database_info['USER'], database_info['PASSWORD'], mechanism='MONGODB-CR')

    return db


class DocumentLock:

    def __init__(self, collection, doc_id, lock_id):
        self._collection = collection
        self._doc_id = doc_id
        self._lock_id = '_lock_{}'.format(lock_id)
        self._db = get_database_connection()

    def lock_document(self):
        prev = self._db[self._collection].find_one_and_update(
            {'_id': ObjectId(self._doc_id)},
            {'$set': {self._lock_id: True}}
        )
        return self._lock_id in prev and prev[self._lock_id]

    def wait_document(self):
        locked = self.lock_document()

        while locked:
            locked = self.lock_document()

    def unlock_document(self):
        self._db[self._collection].find_one_and_update(
            {'_id': ObjectId(self._doc_id)},
            {'$set': {self._lock_id: False}}
        )
