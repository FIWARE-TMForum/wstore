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

from __future__ import unicode_literals

from urlparse import urljoin

from django.db import models
from djangotoolbox.fields import ListField, DictField, EmbeddedModelField

from wstore.models import Organization, Context


# This embedded class is used to save old versions
# of resources to allow downgrades
class ResourceVersion(models.Model):
    version = models.CharField(max_length=20)
    resource_path = models.CharField(max_length=100)
    download_link = models.CharField(max_length=200)


class Resource(models.Model):
    product_id = models.CharField(max_length=100, blank=True, null=True)
    version = models.CharField(max_length=20)  # This field maps the Product Spec version
    provider = models.ForeignKey(Organization)
    content_type = models.CharField(max_length=50)
    download_link = models.URLField()
    resource_path = models.CharField(max_length=100)
    old_versions = ListField(EmbeddedModelField(ResourceVersion))
    state = models.CharField(max_length=20)
    resource_type = models.CharField(max_length=100, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    has_terms = models.BooleanField(default=False)
    meta_info = DictField()
    bundled_assets = ListField()

    def get_url(self):
        return self.download_link

    def get_uri(self):
        site_context = Context.objects.all()[0]
        base_uri = site_context.site.domain

        return urljoin(base_uri, 'charging/api/assetManagement/assets/' + self.pk)

    class Meta:
        app_label = 'wstore'


class ResourcePlugin(models.Model):
    plugin_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    author = models.CharField(max_length=100)
    form = DictField()
    module = models.CharField(max_length=200)
    media_types = ListField(models.CharField(max_length=100))
    formats = ListField(models.CharField(max_length=10))
    overrides = ListField(models.CharField(max_length=10))

    # Whether the plugin must ask for accounting info
    pull_accounting = models.BooleanField(default=False)
    options = DictField()

    def __unicode__(self):
        return self.plugin_id

    class Meta:
        app_label = 'wstore'
