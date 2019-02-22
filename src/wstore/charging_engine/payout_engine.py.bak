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

from __future__ import absolute_import
from __future__ import unicode_literals

from collections import defaultdict
from decimal import Decimal
import time
import threading

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from paypalrestsdk import Payout

from wstore.models import User, Context
from wstore.admin.users.notification_handler import NotificationsHandler
from wstore.charging_engine.models import ReportsPayout, ReportSemiPaid
from wstore.charging_engine.payment_client.paypal_client import PayPalClient
from wstore.store_commons.database import get_database_connection
from wstore.ordering.errors import PayoutError

import requests


class PayoutWatcher(threading.Thread):

    def __init__(self, payouts, reports):
        threading.Thread.__init__(self)
        self.payouts = payouts
        self.reports = reports
        self.notifications = NotificationsHandler()

    def _mark_as_paid(self, report, paid=True):
        headers = {
            'content-type': 'application/json',
            'X-Nick-Name': settings.STORE_NAME,
            'X-Roles': settings.ADMIN_ROLE,
            'X-Email': settings.WSTOREMAIL
        }

        data = [{
            'op': 'replace',
            'path': '/paid',
            'value': paid
        }]

        # Make request
        url = settings.RSS
        if not url.endswith('/'):
            url += '/'

        url += 'rss/settlement/reports/{}'.format(report)

        response = requests.patch(url, json=data, headers=headers)

        if response.status_code != 200:
            print("Error mark as paid report {}: {}".format(report, response.reason))
            return []

        return response.json()

    def _update_status(self, payout):
        rpayout = ReportsPayout.objects.get(payout_id=payout['batch_header']['payout_batch_id'])
        rpayout.status = payout['batch_header']['batch_status']
        rpayout.save()

    def _safe_get_semi_paid(self, report_id):
        try:
            report = ReportSemiPaid.objects.get(report=report_id)
            return report
        except ObjectDoesNotExist:
            r = ReportSemiPaid(report=report_id)
            r.save()
            return r

    def _safe_get_semi_paid_from_item(self, item):
        sender_id = item['payout_item']['sender_item_id']
        report_id = sender_id.split('_')[0]
        return self._safe_get_semi_paid(report_id)

    def _analyze_item(self, item):
        status = item['transaction_status']
        semipaid = self._safe_get_semi_paid_from_item(item)
        pitem = item['payout_item']
        mail = pitem['receiver']

        if status != 'SUCCESS':
            errors = item['errors']

            if mail not in semipaid.failed:
                semipaid.failed.append(mail)
            if mail in semipaid.success:
                semipaid.success.remove(mail)

            semipaid.errors[mail.replace(".", "(dot)")] = {
                'error_message': errors['message'],
                'error_name': errors['name'],
                'item_id': item['payout_item_id'],
                'payout_id': item['payout_batch_id'],
                'transaction_status': status,
                'transaction_id': item['transaction_id']
            }
            semipaid.save()

            try:
                # Only send the notification if it's an user error (DENIED and FAILED?)
                if status in ['DENIED', 'PENDING', 'UNCLAIMED', 'RETURNED', 'ONHOLD', 'BLOCKED', 'FAILED']:
                    self.notifications.send_payout_error(mail, errors['message'])
            except:
                pass

            return False

        if mail in semipaid.failed:
            semipaid.failed.remove(mail)
        if semipaid.errors.get(mail.replace(".", "(dot)")) is not None:
            del semipaid.errors[mail.replace(".", "(dot)")]
        if mail not in semipaid.success:
            semipaid.success.append(mail)
        semipaid.save()

        return True

    def _check_reports_payout(self, payout):
        reports_id = {item['payout_item']['sender_item_id'].split('_')[0] for item in payout['items']}
        for report_id in reports_id:
            filtered = list(filter(lambda x: x.get('id') == int(report_id), self.reports))
            if len(filtered) == 0:
                continue

            report = filtered[0]
            reportmails = [User.objects.get(username=report['ownerProviderId']).email]
            reportmails.extend([User.objects.get(username=stake['stakeholderId']).email for stake in report.get('stakeholders', [])])

            semipaid = self._safe_get_semi_paid(report_id)
            semipaid.failed = [x for x in semipaid.failed if x in reportmails]  # Clean mails not in report
            if len(semipaid.failed) == 0 and all([mail in semipaid.success for mail in reportmails]):
                # Mark as paid in remote
                self._mark_as_paid(report_id)
                # Remove semipaid
                semipaid.delete()
            else:
                semipaid.save()

    def _payout_success(self, payout):
        for item in payout['items']:
            self._analyze_item(item)
        self._check_reports_payout(payout)

    def _check_payout(self, payout):
        try:
            pay = Payout.find(payout['batch_header']['payout_batch_id'])
            status = pay['batch_header']['batch_status']
            self._update_status(pay)
            if status == 'DENIED':
                return False
            if status == 'SUCCESS':
                self._payout_success(pay)
                return False
            if pay['batch_header']['batch_status'] in ['PENDING', 'PROCESSING']:
                return True
            return False
        except Exception:
            return False

    def _check_payouts(self):
        new = []
        for payout in self.payouts:
            pending = self._check_payout(payout)
            if pending:
                # Still pending or processing
                new.append(payout)
        self.payouts = new

    def run(self):
        while len(self.payouts) != 0:
            self._check_payouts()
            time.sleep(1)


class PayoutEngine(object):

    def __init__(self):
        self.paypal = PayPalClient(None)

    def _get_reports(self):
        headers = {
            'content-type': 'application/json',
            'X-Nick-Name': settings.STORE_NAME,
            'X-Roles': settings.ADMIN_ROLE,
            'X-Email': settings.WSTOREMAIL
        }

        data = {
            'aggregatorId': None,
            'providerId': None,
            'productClass': None,
            'onlyPaid': "true"
        }

        # Make request
        url = settings.RSS
        if not url.endswith('/'):
            url += '/'

        url += 'rss/settlement/reports'

        response = requests.get(url, params=data, headers=headers)

        if response.status_code != 200:
            print("Error retrieving reports: {}".format(response.reason))
            return []

        return response.json()

    def _process_reports(self, reports):
        new_reports = defaultdict(lambda: defaultdict(list))
        # Divide by currency
        for report in reports:
            if report['paid']:
                continue
            semipaid = None
            try:
                semipaid = ReportSemiPaid.objects.get(report=report['id'])
            except ObjectDoesNotExist:
                pass

            currency = report['currency']
            usermail = User.objects.get(username=report['ownerProviderId']).email

            if semipaid is None or usermail not in semipaid.success:
                new_reports[currency][usermail].append((report['ownerValue'], report['id']))

            for stake in report['stakeholders']:
                stakemail = User.objects.get(username=stake['stakeholderId']).email

                if semipaid is None or stakemail not in semipaid.success:
                    new_reports[currency][stakemail].append((stake['modelValue'], report['id']))

        return new_reports

    def _process_payouts(self, data):
        db = get_database_connection()
        reference = "__payout__engine__context__lock__"
        # Uses an atomic operation to get and set the _lock value in the purchase
        # document
        pre_value = db.wstore_payout.find_one_and_update(
            {'_id': reference},
            {'$set': {'_lock': True}}
        )

        # If no reference exists, create it
        if pre_value is None:
            db.wstore_payout.insert_one({'_id': reference, '_lock': False})
            pre_value = db.wstore_payout.find_one_and_update(
                {'_id': reference},
                {'$set': {'_lock': True}}
            )

        # If the value of _lock before setting it to true was true, means
        # that the time out function has acquired it previously so the
        # view ends
        if '_lock' in pre_value and pre_value['_lock']:
            raise PayoutError('There is a payout running.')

        payments = []
        context = Context.objects.all()[0]
        current_id = context.payouts_n

        for currency, users in data.items():
            payments.append([])
            for user, values in users.items():
                for value, report in values:
                    sender_id = '{}_{}'.format(report, current_id)
                    payment = {
                        'recipient_type': 'EMAIL',
                        'amount': {
                            'value': "{0:.2f}".format(round(Decimal(value), 2)),
                            'currency': currency
                        },
                        'receiver': user,
                        'sender_item_id': sender_id
                    }
                    current_id += 1
                    payments[-1].append(payment)

        context.payouts_n = current_id
        context.save()

        # _lock is set to false
        db.wstore_payout.find_one_and_update(
            {'_id': reference},
            {'$set': {'_lock': False}}
        )

        return [self.paypal.batch_payout(paybatch) for paybatch in payments]

    def process_reports(self, reports):
        processed = self._process_reports(reports)
        payouts = self._process_payouts(processed)
        to_watch = []

        for payout, created in payouts:
            if not created:
                # Full error, not even said the semipaid because it didn't failed some transaction
                print("Error, batch id: {}".format(payout['sender_batch_header']['sender_batch_id']))  # Log
                continue
            payout_id = payout['batch_header']['payout_batch_id']
            status = payout['batch_header']['batch_status']
            rpayout = ReportsPayout(reports=reports, payout_id=payout_id, status=status)
            rpayout.save()

            to_watch.append(payout)

        if len(to_watch) > 0:
            watcher = PayoutWatcher(to_watch, reports)
            watcher.start()

    def process_unpaid(self):
        reports = self._get_reports()
        self.process_reports(reports)
