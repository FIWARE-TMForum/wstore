# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

import os
import codecs
import subprocess
from copy import deepcopy
from datetime import datetime
from decimal import Decimal

from django.template import loader, Context
from django.conf import settings


class InvoiceBuilder(object):

    def __init__(self, order):
        self._order = order
        self._template_processors = {
            'initial': self._get_initial_parts,
            'recurring': self._get_renovation_parts,
            'usage': self._get_use_parts
        }
        self._context_processors = {
            'initial': self._fill_initial_context,
            'recurring': self._fill_renovation_context,
            'usage': self._fill_use_context
        }

    def _process_subscription_parts(self, applied_parts, parts):
        if 'subscription' in applied_parts:
            for part in applied_parts['subscription']:
                parts['subs_parts'].append(
                    (part['duty_free'], part['tax_rate'], part['value'], part['unit'], unicode(part['renovation_date'])))

    def _process_alteration_parts(self, applied_parts, parts):
        if 'alteration' in applied_parts:
            part = applied_parts['alteration']
            parts['alt_parts'].append(
                (part['type'], deepcopy(part['value']), part.get('period'), deepcopy(part.get('condition'))))

    def _get_initial_parts(self, transaction):
        applied_parts = transaction['related_model']

        # If initial can only contain single payments and subscriptions
        parts = {
            'single_parts': [],
            'subs_parts': [],
            'alt_parts': []
        }
        if 'single_payment' in applied_parts:
            for part in applied_parts['single_payment']:
                parts['single_parts'].append((part['duty_free'], part['tax_rate'], part['value']))

        self._process_subscription_parts(applied_parts, parts)
        self._process_alteration_parts(applied_parts, parts)

        # Get the bill template
        bill_template = loader.get_template('contracting/bill_template_initial.html')
        return parts, bill_template

    def _process_usage_component(self, applied_parts, parts, comp_name, part_name, part_sub):
        # if comp_name in applied_parts and len(applied_parts[comp_name]) > 0:
        parts[part_name] = []
        parts[part_sub] = Decimal(0)

        # Fill use tuples for the invoice
        for part in applied_parts:
            model = part['model']
            unit = model['unit']
            value_unit = model['value']

            # Aggregate use made
            use = Decimal(0)
            for sdr in part['accounting']:
                use += Decimal(sdr['value'])

            parts[part_name].append((unit, value_unit, unicode(use), part['price']))
            parts[part_sub] += Decimal(part['price'])

    def _process_usage_parts(self, applied_parts, parts):
        self._process_usage_component(applied_parts, parts, 'charges', 'use_parts', 'use_subtotal')
        # self._process_usage_component(applied_parts, parts, 'deductions', 'deduct_parts', 'deduct_subtotal')

    def _get_renovation_parts(self, transaction):
        applied_parts = transaction['related_model']

        parts = {
            'subs_parts': [],
            'alt_parts': []
        }
        # If renovation, It contains subscriptions
        self._process_subscription_parts(applied_parts, parts)
        self._process_alteration_parts(applied_parts, parts)

        # Get the bill template
        bill_template = loader.get_template('contracting/bill_template_renovation.html')
        return parts, bill_template

    def _get_use_parts(self, transaction):
        applied_parts = transaction['applied_accounting']

        # If use, can only contain pay per use parts or deductions
        parts = {
            'use_parts': [],
            'alt_parts': [],
            'use_subtotal': 0
        }
        self._process_usage_parts(applied_parts, parts)
        self._process_alteration_parts(applied_parts, parts)

        # Get the bill template
        bill_template = loader.get_template('contracting/bill_template_use.html')
        return parts, bill_template

    def _fill_alts_context(self, context, parts):
        compare_table = {'eq': '=', 'lt': '<', 'gt': '>', 'le': '<=', 'ge': '>='}

        def cond_to_str(cond):
            if cond is not None:
                cond['operation'] = compare_table.get(cond['operation'])
                return "{op} {val}".format(op=cond['operation'], val=cond['value'])
            else:
                return ""

        def value_to_str(val):
            if isinstance(val, dict):
                val = 'Value: {v} {cur}. Duty free: {d} {cur}'.format(v=val['value'], d=val['duty_free'], cur=context['cur'])
            else:
                val = '{} %'.format(val)
            return val

        alts = parts.get('alt_parts', [])
        alts = [(x[0], value_to_str(x[1]), x[2], cond_to_str(x[3])) for x in alts]

        context['fees'] = [x for x in alts if x[0] == 'fee']
        context['discounts'] = [x for x in alts if x[0] == 'discount']

        context['exists_fees'] = len(context['fees']) > 0
        context['exists_discounts'] = len(context['discounts']) > 0

    def _fill_initial_context(self, context, parts):
        context['exists_single'] = False
        context['exists_subs'] = False

        def assign_if_exists(name):
            partsname = '{}_parts'.format(name)
            if len(parts[partsname]) > 0:
                context[partsname] = parts[partsname]
                context['exists_{}'.format(name)] = True

        assign_if_exists('single')
        assign_if_exists('subs')
        self._fill_alts_context(context, parts)

    def _fill_renovation_context(self, context, parts):
        context['subs_parts'] = parts['subs_parts']
        self._fill_alts_context(context, parts)

    def _fill_use_context(self, context, parts):
        context['use_parts'] = parts['use_parts']
        self._fill_alts_context(context, parts)

        context['use_subtotal'] = unicode(parts['use_subtotal'])

        if 'deduct_parts' in parts:
            context['deduction'] = True
            context['deduct_parts'] = parts['deduct_parts']
            context['deduct_subtotal'] = parts['deduct_subtotal']
        else:
            context['deduction'] = False

    def _avoid_existing_name(self, name, ix):
        new_name = name + '_' + unicode(ix) + '.pdf'
        path = os.path.join(settings.BILL_ROOT, new_name)

        if os.path.exists(path):
            path, new_name = self._avoid_existing_name(name, ix + 1)

        return path, new_name

    def generate_invoice(self, contract, transaction, type_):
        """
        Create a PDF invoice based on the price components used to charge the user
        :param transaction: Total amount charged to the customer
        :param type_: Type of the charge, initial, renovation, pay-per-use
        """

        # Get invoice context parts and invoice template
        parts, bill_template = self._template_processors[type_](transaction)

        tax = self._order.tax_address
        customer_profile = self._order.customer.userprofile

        if contract.last_charge is None:
            # If last charge is None means that it is the invoice generation
            # associated with a free offering
            date = unicode(datetime.utcnow()).split(' ')[0]
        else:
            date = unicode(contract.last_charge).split(' ')[0]

        # Calculate total taxes applied
        tax_value = Decimal(transaction['price']) - Decimal(transaction['duty_free'])

        # Load pricing info into the context
        context = {
            'basedir': settings.BASEDIR,
            'offering_name': contract.offering.name,
            'off_organization': contract.offering.owner_organization.name,
            'off_version': contract.offering.version,
            'ref': self._order.pk,
            'date': date,
            'organization': customer_profile.current_organization.name,
            'customer': customer_profile.complete_name,
            'address': tax.get('street'),
            'postal': tax.get('postal'),
            'city': tax.get('city'),
            'province': tax.get('province'),
            'country': tax.get('country'),
            'subtotal': transaction['duty_free'],
            'tax': unicode(tax_value),
            'total': transaction['price'],
            'cur': transaction['currency']  # General currency of the invoice
        }

        # Include the corresponding parts in the context
        # depending on the type of applied parts
        self._context_processors[type_](context, parts)

        # Render the invoice template
        bill_code = bill_template.render(Context(context))

        # Create the bill code file
        invoice_id = self._order.pk + '_' + contract.item_id + '_' + date
        raw_invoice_path = os.path.join(settings.BILL_ROOT, invoice_id + '.html')

        f = codecs.open(raw_invoice_path, 'wb', 'utf-8')
        f.write(bill_code)
        f.close()

        invoice_path, invoice_name = self._avoid_existing_name(invoice_id, 0)

        # Compile the bill file
        subprocess.call([settings.BASEDIR + '/create_invoice.sh', raw_invoice_path, invoice_path])

        # Remove temporal files
        for file_ in os.listdir(settings.BILL_ROOT):

            if not file_.endswith('.pdf'):
                os.remove(os.path.join(settings.BILL_ROOT, file_))

        return os.path.join(settings.MEDIA_URL, 'bills/' + invoice_name)
