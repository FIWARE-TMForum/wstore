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



from shutil import rmtree

from functools import wraps


def installPluginRollback(func):

    class Logger(object):
        _state = {}

        def get_state(self):
            return self._state

        def log_action(self, action, value):
            self._state[action] = value

    @wraps(func)
    def wrapper(self, path, logger=None):
        try:
            logger = Logger()
            result = func(self, path, logger=logger)
        except Exception as e:
            # Remove directory if existing
            if 'PATH' in logger.get_state():
                rmtree(logger.get_state()['PATH'], True)

            if 'MODEL' in logger.get_state():
                logger.get_state()['MODEL'].delete()

            # Raise the exception
            raise(e)
        return result

    return wrapper
