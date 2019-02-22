# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

import urllib.request, urllib.parse, urllib.error
import urllib.parse

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


def is_valid_url(url):
    valid = True
    validator = URLValidator()
    try:
        validator(url)
    except ValidationError:
        valid = False

    return valid


def url_fix(s, charset='utf-8'):
    if isinstance(s, str):
        s = s.encode(charset, 'ignore')

    scheme, netloc, path, qs, anchor = urllib.parse.urlsplit(s)

    path = urllib.parse.quote(path, '/%')
    qs = urllib.parse.quote_plus(qs, ':&=')

    return urllib.parse.urlunsplit((scheme, netloc, path, qs, anchor))


def add_slash(url):
    if url[-1] != '/':
        url += '/'

    return url
