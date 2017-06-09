# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid

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

from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from djangotoolbox.fields import ListField
from djangotoolbox.fields import DictField, EmbeddedModelField
from django.db import models

from wstore.charging_engine.models import *


class Context(models.Model):

    site = models.OneToOneField(Site, related_name='site')
    local_site = models.OneToOneField(Site, related_name='local_site', null=True, blank=True)
    top_rated = ListField()
    newest = ListField()
    user_refs = DictField()
    failed_cdrs = ListField()
    payouts_n = models.IntegerField(default=0)

    def is_valid_currency(self, currency):
        """
         Checks that a currency is valid for WStore
       """
        valid = False
        if 'allowed' in self.allowed_currencies and len(self.allowed_currencies['allowed']) > 0:
            for c in self.allowed_currencies['allowed']:
                if c['currency'].lower() == currency.lower():
                    valid = True
                    break
        return valid


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
        return Context.objects.all()[0].site.domain + '/partyManagement/' + party_type + '/' + self.name


from wstore.asset_manager.models import Resource, ResourcePlugin


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


def create_context(sender, instance, created, **kwargs):

    if created:
        if not len(Context.objects.all()):
            context = Context.objects.get_or_create(site=instance)[0]
            context.save()
        else:
            context = Context.objects.all()[0]
            context.local_site = instance
            context.save()


# Creates a new user profile when an user is created
post_save.connect(create_user_profile, sender=User)


# Creates a context when the site is created
post_save.connect(create_context, sender=Site)
