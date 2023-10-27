# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

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

import re
from distutils.version import StrictVersion

VERSION_REGEXP = re.compile(r"^(?:[1-9]\d*\.|0\.)*(?:[1-9]\d*|0)$")


def _fix_digit_version(version):
    # Adds minor release to version numbers that are just integers.
    return version + ".0" if version.isdigit() else version


def is_valid_version(version):
    # Unlike StrictVersion objects, single integer versions are allowed.
    return re.match(VERSION_REGEXP, version)


def is_lower_version(version1, version2):
    # Strict version does not allow single integer versions
    # so it is neecesary to fix them.
    # Code line is kept long here so the "fixing" of version numbers remains
    # explicit.
    return StrictVersion(_fix_digit_version(version1)) < StrictVersion(_fix_digit_version(version2))


def version_cmp(version1, version2):
    # Strict version does not allow single integer versions
    # so it is neecesary to fix them.
    # Code line is kept long here so the "fixing" of version numbers remains
    # explicit.
    return StrictVersion(_fix_digit_version(version1))._cmp(StrictVersion(_fix_digit_version(version2)))


def key_fun_version(comparator, object_instance=False):
    class key:
        def __init__(self, obj, *args):
            self.obj = obj
            if object_instance:
                self.obj = obj.version

        def __lt__(self, other):
            return comparator(self.obj, other.obj) < 0

        def __gt__(self, other):
            return comparator(self.obj, other.obj) > 0

        def __eq__(self, other):
            return comparator(self.obj, other.obj) == 0

        def __le__(self, other):
            return comparator(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return comparator(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return comparator(self.obj, other.obj) != 0

    return key
