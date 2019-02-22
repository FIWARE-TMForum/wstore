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



from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from djangotoolbox.fields import ListField
from djangotoolbox.fields import DictField, EmbeddedModelField
from django.db import models

from wstore.charging_engine.models import *


class Context(models.Model):
    user_refs = DictField()
    failed_cdrs = ListField()
    failed_upgrades = ListField()
    payouts_n = models.IntegerField(default=0)


class Organization(models.Model):

    name = models.CharField(max_length=50, unique=True)
    notification_url = models.CharField(max_length=300, null=True, blank=True)
    acquired_offerings = ListField()
    private = models.BooleanField(default=True)
    correlation_number = models.IntegerField(default=0)
    tax_address = DictField()
    managers = ListField()
    actor_id = models.CharField(null=True, blank=True, max_length=100)

    expenditure_limits = DictField()

    def get_party_url(self):
        party_type = 'individual' if self.private else 'organization'
        parsed_site = urlparse(settings.SITE)
        return '{}://{}/partyManagement/{}/{}'.format(parsed_site.scheme, parsed_site.netloc, party_type, self.name)


from wstore.asset_manager.models import Resource, ResourceVersion, ResourcePlugin


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    current_organization = models.ForeignKey(Organization)
    complete_name = models.CharField(max_length=100)
    actor_id = models.CharField(null=True, blank=True, max_length=100)
    current_roles = ListField()
    access_token = models.CharField(max_length=150, null=True, blank=True)

    def get_current_roles(self):
        return self.current_roles


def create_user_profile(sender, instance, created, **kwargs):

    if created:
        # Create a private organization for the user
        default_organization = Organization.objects.get_or_create(name=instance.username)
        default_organization[0].managers.append(instance.pk)
        default_organization[0].save()

        profile, created = UserProfile.objects.get_or_create(
            user=instance,
            current_roles=['customer'],
            current_organization=default_organization[0]
        )
        if instance.first_name and instance.last_name:
            profile.complete_name = instance.first_name + ' ' + instance.last_name
            profile.save()


# Creates a new user profile when an user is created
post_save.connect(create_user_profile, sender=User)
