# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid
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
"""
This file contains the django models for the Revenue Sharing/Settlement System
(RSS). Model fields are in camelCase, breaking python convention for easier
compatibility and consistency with the API.
"""

from djongo import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class RSSValidators:
    @staticmethod
    def validate_stakeholders(stakeholders):
        stakeholder_ids = {st["stakeholderId"] for st in stakeholders}
        if len(stakeholder_ids) < len(stakeholders):
            raise ValidationError("All stakeholders must be unique.", params={"stakeholders": stakeholders})

    @staticmethod
    def validate_type(type):
        def validator(field):
            if not isinstance(field, type):
                raise ValidationError(f"{field} is not of type {type}")

        return validator


class Provider(models.Model):
    stakeholderId = models.CharField(
        max_length=100, primary_key=True, blank=False, validators=[RSSValidators.validate_type(str)]
    )
    stakeholderValue = models.DecimalField(
        max_digits=7, decimal_places=4, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    class Meta:
        managed = False


class RSSModel(models.Model):
    ownerProviderId = models.CharField(max_length=100, blank=False, validators=[RSSValidators.validate_type(str)])
    productClass = models.CharField(max_length=100, blank=False, validators=[RSSValidators.validate_type(str)])
    algorithmType = models.CharField(
        max_length=100, default="FIXED_PERCENTAGE", validators=[RSSValidators.validate_type(str)]
    )
    ownerValue = models.DecimalField(
        max_digits=7, decimal_places=4, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    aggregatorValue = models.DecimalField(
        max_digits=7, decimal_places=4, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    stakeholders = models.ArrayField(
        model_container=Provider, default=list, blank=True, validators=[RSSValidators.validate_stakeholders]
    )

    class Meta:
        unique_together = ("ownerProviderId", "productClass")

    def validate_value_sum(self):
        stakeholder_value_sum = sum(map(lambda stakeholder: stakeholder["stakeholderValue"], self.stakeholders))
        if stakeholder_value_sum + self.aggregatorValue + self.ownerValue != 100.0:
            raise ValidationError(
                "The sum of percentages for the aggregator, owner and stakeholders must equal 100. "
                f"{self.aggregatorValue} + {self.ownerValue} + {stakeholder_value_sum} != 100"
            )

    def save(self, *args, **kwargs):
        self.validate_value_sum()
        super(RSSModel, self).save(*args, **kwargs)


class CDR(models.Model):
    """
    Model for a Charging Data Record.
    """

    class TransactionTypes(models.TextChoices):
        C = "C", "Charge"
        R = "R", "Refund"

    productClass = models.CharField(max_length=100)
    correlationNumber = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    application = models.CharField(max_length=100)
    transactionType = models.CharField(max_length=1, choices=TransactionTypes.choices, default=TransactionTypes.C)
    event = models.CharField(max_length=100)
    referenceCode = models.CharField(max_length=100)
    description = models.TextField()
    chargedAmount = models.DecimalField(max_digits=20, decimal_places=10)
    chargedTaxAmount = models.DecimalField(max_digits=20, decimal_places=10)
    currency = models.CharField(max_length=100)
    customerId = models.CharField(max_length=100)
    appProviderId = models.CharField(max_length=100)


class Provider(models.Model):
    ...
