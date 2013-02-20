from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from djangotoolbox.fields import ListField
from djangotoolbox.fields import DictField

from fiware_store.markets.models import *
from fiware_store.repositories.models import *
from fiware_store.offerings.models import *
from fiware_store.contracting.models import *


class Organization(models.Model):

    name = models.CharField(max_length=50, unique=True)
    offerings_purchased = ListField()


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    organization = models.ForeignKey(Organization, blank=True, null=True)  # an user could belong to more than one organization FIXME
    roles = ListField()
    offerings_purchased = ListField()
    offerings_provided = ListField()
    tax_address = DictField()
    complete_name = models.CharField(max_length=100)


def create_user_profile(sender, instance, created, **kwargs):

    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance, roles=['customer'])

#Creates a new user profile when an user is created
post_save.connect(create_user_profile, sender=User)
