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

from __future__ import unicode_literals
from __future__ import absolute_import

from collections import namedtuple

from mock import MagicMock, call
from nose_parameterized import parameterized

from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from wstore.charging_engine import payout_engine
from wstore.ordering.errors import PayoutError


class ReportSemiPaid:
    def __init__(self, report=1, failed=None, success=None, errors=None):
        if failed is None:
            failed = []
        if success is None:
            success = []
        if errors is None:
            errors = {}
        self.report = report
        self.failed = failed
        self.success = success
        self.errors = errors
        self.save = MagicMock()
        self.delete = MagicMock()

ReportsPayout = namedtuple('ReportsPayout', ['reports', 'payout_id', 'status', 'save'])


def createMail(i):
    return "user{}@email.com".format(i)


def createUsers(*args):
    return [namedtuple('User', ['email'])(createMail(x)) for x in args]


def createReport(ids, owner=1, stakeholders=None):
    if stakeholders is None:
        stakeholders = []
    return {
        'id': ids,
        'ownerProviderId': createMail(owner),
        'stakeholders': [{'stakeholderId': createMail(x)} for x in stakeholders]
    }


def createItem(status, receiver='user1@email.com', itemid='report1_123', payout='itemID0', batch='batchID0', transaction='transID0'):
    return {
        'transaction_status': status,
        'payout_item': {
            'receiver': receiver,
            'sender_item_id': itemid
        },
        'payout_item_id': payout,
        'payout_batch_id': batch,
        'transaction_id': transaction,
        'errors': {
            'message': "An error",
            'name': 'ERROR'
        }
    }


def createErrorSaved(status, message='An error', name='ERROR', item='itemID0', payout='batchID0', transaction='transID0'):
    return {
        'error_message': message,
        'error_name': name,
        'item_id': item,
        'payout_id': payout,
        'transaction_status': status,
        'transaction_id': transaction
    }


def RSSUrl():
    url = settings.RSS
    if url.endswith("/"):
        url = url[:-1]
    return url


def setUp():
    # Libraries
    payout_engine.threading = MagicMock()
    payout_engine.requests = MagicMock()
    payout_engine.Payout = MagicMock()

    # Models
    payout_engine.User = MagicMock()
    payout_engine.Context = MagicMock()
    payout_engine.ReportsPayout = MagicMock()
    payout_engine.ReportSemiPaid = MagicMock()

    # Inner library
    payout_engine.NotificationsHandler = MagicMock()
    payout_engine.PayPalClient = MagicMock()
    payout_engine.get_database_connection = MagicMock()


class PayoutWatcherTestCase(TestCase):

    tags = ('payout', 'payout-watcher')

    def setUp(self):
        setUp()

    def test_mark_as_paid(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.requests.patch().status_code = 200
        payout_engine.requests.patch().json.return_value = [{'test': 'case'}]

        payout_engine.requests.patch.reset_mock()

        result = watcher._mark_as_paid("report1")

        url = "{}/rss/settlement/reports/{}".format(RSSUrl(), "report1")

        payout_engine.requests.patch.assert_called_once_with(
            url,
            json=[{'op': 'replace', 'path': '/paid', 'value': True}],
            headers={
                'content-type': 'application/json',
                'X-Nick-Name': settings.STORE_NAME,
                'X-Roles': 'provider',
                'X-Email': settings.WSTOREMAIL})

        payout_engine.requests.patch().json.assert_called_once_with()

        assert result == [{'test': 'case'}]

    def test_mark_as_paid_error(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.requests.patch().status_code = 404
        payout_engine.requests.patch().json.return_value = [{'test': 'case'}]

        payout_engine.requests.patch.reset_mock()

        result = watcher._mark_as_paid("report1")

        url = "{}/rss/settlement/reports/{}".format(RSSUrl(), "report1")

        payout_engine.requests.patch.assert_called_once_with(
            url,
            json=[{'op': 'replace', 'path': '/paid', 'value': True}],
            headers={
                'content-type': 'application/json',
                'X-Nick-Name': settings.STORE_NAME,
                'X-Roles': 'provider',
                'X-Email': settings.WSTOREMAIL})

        payout_engine.requests.patch().json.assert_not_called()

        assert result == []

    def test_update_status(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout = MagicMock()
        watcher._update_status(payout)

        payout.__getitem__.assert_has_calls([call('batch_header'), call('batch_header')], any_order=True)
        payout['batch_header'].__getitem__.assert_has_calls([call('payout_batch_id'), call('batch_status')])

    def test_get_semi_paid_correct(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.ReportSemiPaid.objects.get.return_value = 'reportobject'

        report = watcher._safe_get_semi_paid('report1')

        payout_engine.ReportSemiPaid.objects.get.assert_called_once_with(report="report1")
        assert report == 'reportobject'

    def test_get_semi_paid_not_exist(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.ReportSemiPaid.objects.get.side_effect = ObjectDoesNotExist()

        watcher._safe_get_semi_paid('report1')

        payout_engine.ReportSemiPaid.objects.get.assert_called_once_with(report='report1')
        payout_engine.ReportSemiPaid.assert_called_once_with(report='report1')
        payout_engine.ReportSemiPaid().save.assert_called_once_with()

    def test_get_semi_paid_from_item(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.ReportSemiPaid.objects.get.return_value = 'reportobject'

        report = watcher._safe_get_semi_paid_from_item({'payout_item': {'sender_item_id': 'report1_123'}})

        payout_engine.ReportSemiPaid.objects.get.assert_called_once_with(report='report1')
        assert report == 'reportobject'

    def test_get_semi_paid_from_item_not_exist(self):
        watcher = payout_engine.PayoutWatcher([], [])
        payout_engine.ReportSemiPaid.objects.get.side_effect = ObjectDoesNotExist()

        watcher._safe_get_semi_paid_from_item({'payout_item': {'sender_item_id': 'report1_123'}})

        payout_engine.ReportSemiPaid.objects.get.assert_called_once_with(report='report1')
        payout_engine.ReportSemiPaid.assert_called_once_with(report='report1')
        payout_engine.ReportSemiPaid().save.assert_called_once_with()

    def test_analyze_item_status_error_not_notify(self):
        watcher = payout_engine.PayoutWatcher([], [])
        semipaid = ReportSemiPaid()

        payout_engine.ReportSemiPaid.objects.get.return_value = semipaid

        item = createItem('ERROR')
        itemr = watcher._analyze_item(item)

        assert not itemr
        assert semipaid.failed == ['user1@email.com']
        assert semipaid.success == []
        assert semipaid.errors.get("user1@email(dot)com") == createErrorSaved('ERROR')
        semipaid.save.assert_called_once_with()
        watcher.notifications.send_payout_error.assert_not_called()

    def test_analyze_item_status_error_clean_semipaid(self):
        watcher = payout_engine.PayoutWatcher([], [])
        semipaid = ReportSemiPaid(1, ['user1@email.com', 'user2@email.com'], ['user1@email.com', 'user3@email.com'], {'user1@email(dot)com': {}})

        payout_engine.ReportSemiPaid.objects.get.return_value = semipaid

        item = createItem("ERROR")
        itemr = watcher._analyze_item(item)

        assert not itemr
        assert semipaid.failed == ['user1@email.com', 'user2@email.com']
        assert semipaid.success == ['user3@email.com']
        assert semipaid.errors.get("user1@email(dot)com") == createErrorSaved("ERROR")
        semipaid.save.assert_called_once_with()

    @parameterized.expand(['DENIED', 'PENDING', 'UNCLAIMED', 'RETURNED', 'ONHOLD', 'BLOCKED', 'FAILED'])
    def test_analyze_item_status_error_notify(self, status):
        watcher = payout_engine.PayoutWatcher([], [])
        semipaid = ReportSemiPaid()

        payout_engine.ReportSemiPaid.objects.get.return_value = semipaid

        item = createItem(status)
        itemr = watcher._analyze_item(item)

        assert not itemr
        assert semipaid.failed == ['user1@email.com']
        assert semipaid.success == []
        assert semipaid.errors.get("user1@email(dot)com") == createErrorSaved(status)
        semipaid.save.assert_called_once_with()
        watcher.notifications.send_payout_error.assert_called_once_with('user1@email.com', 'An error')

    def test_analyze_item_correct(self):
        watcher = payout_engine.PayoutWatcher([], [])
        semipaid = ReportSemiPaid()
        payout_engine.ReportSemiPaid.objects.get.return_value = semipaid

        item = createItem("SUCCESS")
        itemr = watcher._analyze_item(item)

        assert itemr
        assert semipaid.failed == []
        assert semipaid.success == ['user1@email.com']
        assert semipaid.errors.get('user1@email(dot)com') is None
        semipaid.save.assert_called_once_with()

    def test_analyze_item_correct_fix_semipaid(self):
        watcher = payout_engine.PayoutWatcher([], [])
        semipaid = ReportSemiPaid(1, ['user1@email.com', 'user2@email.com'], ['user1@email.com', 'user3@email.com'], {'user1@email(dot)com': {}, 'user2@email(dot)com': {}})
        payout_engine.ReportSemiPaid.objects.get.return_value = semipaid

        item = createItem("SUCCESS")
        itemr = watcher._analyze_item(item)

        assert itemr
        assert semipaid.failed == ['user2@email.com']
        assert semipaid.success == ['user1@email.com', 'user3@email.com']
        assert semipaid.errors.get('user1@email(dot)com') is None
        assert semipaid.errors.get('user2@email(dot)com') == {}
        semipaid.save.assert_called_once_with()

    def test_check_reports_payout_not_finished(self):
        payout = {'items': [{'payout_item': {'sender_item_id': '9_123'}}]}
        reports = [createReport(9), createReport(10, 2)]
        watcher = payout_engine.PayoutWatcher([], reports)
        watcher._safe_get_semi_paid = MagicMock()
        semipaid = ReportSemiPaid(1, ['user1@email.com', 'user2@email.com'])
        watcher._safe_get_semi_paid.return_value = semipaid
        watcher._mark_as_paid = MagicMock()
        payout_engine.User.objects.get.side_effect = createUsers(1)

        watcher._check_reports_payout(payout)

        payout_engine.User.objects.get.assert_called_once_with(username='user1@email.com')
        watcher._safe_get_semi_paid.assert_called_once_with('9')

        assert semipaid.failed == ['user1@email.com']  # Bad emails cleaned
        watcher._mark_as_paid.assert_not_called()
        semipaid.delete.assert_not_called()
        semipaid.save.assert_called_once_with()

    def test_check_reports_payout_finished(self):
        # Only owner and it is in the report in success, so it is full paid
        payout = {'items': [{'payout_item': {'sender_item_id': '9_123'}}]}
        reports = [createReport(9), createReport(10, 2)]
        watcher = payout_engine.PayoutWatcher([], reports)

        watcher._safe_get_semi_paid = MagicMock()
        semipaid = ReportSemiPaid(1, ['user2@email.com'], ['user1@email.com'])
        watcher._safe_get_semi_paid.return_value = semipaid

        watcher._mark_as_paid = MagicMock()
        payout_engine.User.objects.get.side_effect = createUsers(1)

        watcher._check_reports_payout(payout)

        payout_engine.User.objects.get.assert_called_once_with(username='user1@email.com')
        watcher._safe_get_semi_paid.assert_called_once_with('9')

        assert semipaid.failed == []  # Bad emails cleaned
        watcher._mark_as_paid.assert_called_once_with('9')
        semipaid.delete.assert_called_once_with()
        semipaid.save.assert_not_called()

    def test_check_reports_payout_not_finished_stakeholders(self):
        # Owner success, but not stakeholders
        payout = {'items': [{'payout_item': {'sender_item_id': '9_123'}}]}
        reports = [createReport(9, 1, [2, 3]), createReport(10, 4)]
        watcher = payout_engine.PayoutWatcher([], reports)

        semipaid = ReportSemiPaid(1, ['user2@email.com', 'user3@email.com', 'notexist@email.com'], ['user1@email.com'])
        watcher._safe_get_semi_paid = MagicMock(return_value=semipaid)

        watcher._mark_as_paid = MagicMock()
        payout_engine.User.objects.get.side_effect = createUsers(1, 2, 3)

        watcher._check_reports_payout(payout)

        payout_engine.User.objects.get.assert_has_calls([call(username='user1@email.com'), call(username='user2@email.com'), call(username='user3@email.com')])
        watcher._safe_get_semi_paid.assert_called_once_with('9')

        assert semipaid.failed == ['user2@email.com', 'user3@email.com']  # Bad emails cleaned
        watcher._mark_as_paid.assert_not_called()
        semipaid.delete.assert_not_called()
        semipaid.save.assert_called_once_with()

    def test_check_reports_payout_successs_stakeholders(self):
        # Owner success, but not stakeholders
        payout = {'items': [{'payout_item': {'sender_item_id': '9_123'}}]}
        reports = [createReport(9, 1, [2, 3]), createReport(10, 4)]
        watcher = payout_engine.PayoutWatcher([], reports)

        semipaid = ReportSemiPaid(1, ['notexist@email.com'], [createMail(1), createMail(2), createMail(3)])
        watcher._safe_get_semi_paid = MagicMock(return_value=semipaid)

        watcher._mark_as_paid = MagicMock()
        payout_engine.User.objects.get.side_effect = createUsers(1, 2, 3)

        watcher._check_reports_payout(payout)

        payout_engine.User.objects.get.assert_has_calls([call(username='user1@email.com'), call(username='user2@email.com'), call(username='user3@email.com')])
        watcher._safe_get_semi_paid.assert_called_once_with('9')

        assert semipaid.failed == []  # Bad emails cleaned
        watcher._mark_as_paid.assert_called_once_with('9')
        semipaid.delete.assert_called_once_with()
        semipaid.save.assert_not_called()

    def test_payout_success(self):
        watcher = payout_engine.PayoutWatcher([], [])
        watcher._analyze_item = MagicMock()
        watcher._check_reports_payout = MagicMock()

        payout = {'items': ['item1', 'item2', 'item3', 'otheritem']}

        watcher._payout_success(payout)

        watcher._analyze_item.assert_has_calls([call(x) for x in payout['items']])
        watcher._check_reports_payout.assert_called_once_with(payout)

    @parameterized.expand([
        ('DENIED', False, False),
        ('UNKNOWN', False, False),
        ('PENDING', True, False),
        ('PROCESSING', True, False),
        ('SUCCESS', False, True)])
    def test_check_payout_denied(self, status, must_cont, success):
        watcher = payout_engine.PayoutWatcher([], [])
        watcher._update_status = MagicMock()
        watcher._payout_success = MagicMock()

        pay = {'batch_header': {'batch_status': status}}
        payout_engine.Payout.find.return_value = pay
        payout = {'batch_header': {'payout_batch_id': 'batchID0'}}
        cont = watcher._check_payout(payout)

        assert cont == must_cont
        payout_engine.Payout.find.assert_called_once_with('batchID0')
        watcher._update_status.assert_called_once_with(pay)
        if success:
            watcher._payout_success.assert_called_once_with(pay)
        else:
            watcher._payout_success.assert_not_called()

    def test_check_payouts(self):
        watcher = payout_engine.PayoutWatcher(['payout1', 'payout2', 'payout3', 'payout4'], [])
        watcher._check_payout = MagicMock()
        # Keep watching first and third
        watcher._check_payout.side_effect = [True, False, True, False]

        assert watcher.payouts == ['payout1', 'payout2', 'payout3', 'payout4']
        watcher._check_payouts()
        watcher._check_payout.assert_has_calls([call('payout1'), call('payout2'), call('payout3'), call('payout4')])
        assert watcher.payouts == ['payout1', 'payout3']

        watcher._check_payout.side_effect = [False, False]
        watcher._check_payouts()
        watcher._check_payout.assert_has_calls([call('payout1'), call('payout3')])
        assert watcher.payouts == []


class PayoutEngineTestCase(TestCase):

    tags = ('payout', 'payout-engine')

    def setUp(self):
        setUp()
        self.oldPayoutWatcher = payout_engine.PayoutWatcher
        payout_engine.PayoutWatcher = MagicMock()
        self.reference = '__payout__engine__context__lock__'

    def tearDown(self):
        payout_engine.PayoutWatcher = self.oldPayoutWatcher  # Recover the original implementation

    def test_get_reports_not_paid(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.requests.get().status_code = 200
        payout_engine.requests.get().json.return_value = [{'test': 'case'}]

        payout_engine.requests.get.reset_mock()

        result = engine._get_reports()

        url = "{}/rss/settlement/reports".format(RSSUrl())

        payout_engine.requests.get.assert_called_once_with(
            url,
            params={'aggregatorId': None, 'providerId': None, 'productClass': None, 'onlyPaid': "true"},
            headers={
                'content-type': 'application/json',
                'X-Nick-Name': settings.STORE_NAME,
                'X-Roles': 'provider',
                'X-Email': settings.WSTOREMAIL})

        payout_engine.requests.get().json.assert_called_once_with()

        assert result == [{'test': 'case'}]

    def test_process_reports_all_paid(self):
        engine = payout_engine.PayoutEngine()
        reports = [{
            'paid': True,
            'id': 1,
            'currency': 'EUR',
            'ownerProviderId': createMail(1),
            'stakeholders': []
        }, {
            'paid': True,
            'id': 2,
            'currency': 'EUR',
            'ownerProviderId': createMail(2),
            'stakeholders': []
        }]

        new_reports = engine._process_reports(reports)

        assert new_reports == {}

        payout_engine.ReportSemiPaid.objets.get.assert_not_called()
        payout_engine.User.objets.get.assert_not_called()

    def test_process_reports_simple(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.ReportSemiPaid.objects.get.side_effect = ObjectDoesNotExist()
        payout_engine.User.objects.get.side_effect = createUsers(1)

        reports = [{
            'paid': False,
            'id': 1,
            'currency': 'EUR',
            'ownerProviderId': createMail(1),
            'ownerValue': 10,
            'stakeholders': []
        }]
        new_reports = engine._process_reports(reports)

        # Just one report
        assert new_reports == {'EUR': {'user1@email.com': [(10, 1)]}}
        payout_engine.ReportSemiPaid.objects.get.assert_called_once_with(report=1)
        payout_engine.User.objects.get.assert_called_once_with(username=createMail(1))

    @parameterized.expand([
        (('EUR', 'EUR'), {'EUR': {'user1@email.com': [(10, 1), (20, 2)]}}),
        (('EUR', 'USD'), {'EUR': {'user1@email.com': [(10, 1)]}, 'USD': {'user1@email.com': [(20, 2)]}})
    ])
    def test_process_reports_multiple_pays_user(self, currencies, result):
        engine = payout_engine.PayoutEngine()
        payout_engine.ReportSemiPaid.objects.get.side_effect = ObjectDoesNotExist()
        payout_engine.User.objects.get.side_effect = createUsers(1, 1)

        reports = [{
            'paid': False,
            'id': 1,
            'currency': currencies[0],
            'ownerProviderId': createMail(1),
            'ownerValue': 10,
            'stakeholders': []
        }, {
            'paid': False,
            'id': 2,
            'currency': currencies[1],
            'ownerProviderId': createMail(1),
            'ownerValue': 20,
            'stakeholders': []
        }]
        new_reports = engine._process_reports(reports)

        assert new_reports == result
        payout_engine.ReportSemiPaid.objects.get.assert_has_calls([call(report=1), call(report=2)])
        payout_engine.User.objects.get.assert_has_calls([call(username=createMail(1)), call(username=createMail(1))])

    def test_process_reports_with_stakeholders(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.ReportSemiPaid.objects.get.side_effect = ObjectDoesNotExist()
        payout_engine.User.objects.get.side_effect = createUsers(1, 2, 3, 2, 1)

        reports = [{
            'paid': False,
            'id': 1,
            'currency': 'EUR',
            'ownerProviderId': createMail(1),
            'ownerValue': 10,
            'stakeholders': [{
                'stakeholderId': createMail(2),
                'modelValue': 2
            }, {
                'stakeholderId': createMail(3),
                'modelValue': 4
            }]
        }, {
            'paid': False,
            'id': 2,
            'currency': 'EUR',
            'ownerProviderId': createMail(2),
            'ownerValue': 20,
            'stakeholders': [{
                'stakeholderId': createMail(1),
                'modelValue': 10
            }]
        }]

        new_reports = engine._process_reports(reports)

        assert new_reports == {'EUR': {'user1@email.com': [(10, 1), (10, 2)], 'user2@email.com': [(2, 1), (20, 2)], 'user3@email.com': [(4, 1)]}}
        payout_engine.ReportSemiPaid.objects.get.assert_has_calls([call(report=1), call(report=2)])
        payout_engine.User.objects.get.assert_has_calls([call(username=createMail(1)), call(username=createMail(2)), call(username=createMail(3)), call(username=createMail(2)), call(username=createMail(1))])

    def test_process_reports_user_in_semipaid(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.ReportSemiPaid.objects.get.return_value = ReportSemiPaid(1, None, [createMail(1)])
        payout_engine.User.objects.get.side_effect = createUsers(1)

        reports = [{
            'paid': False,
            'id': 1,
            'currency': 'EUR',
            'ownerProviderId': createMail(1),
            'ownerValue': 10,
            'stakeholders': []
        }]

        new_reports = engine._process_reports(reports)

        assert new_reports == {}
        payout_engine.ReportSemiPaid.objects.get.assert_has_calls([call(report=1)])
        payout_engine.User.objects.get.assert_has_calls([call(username=createMail(1))])

    def test_process_reports_user_in_semipaid_and_stakeholders(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.ReportSemiPaid.objects.get.return_value = ReportSemiPaid(1, None, [createMail(1), createMail(3)])
        payout_engine.User.objects.get.side_effect = createUsers(1, 2, 3)

        reports = [{
            'paid': False,
            'id': 1,
            'currency': 'EUR',
            'ownerProviderId': createMail(1),
            'ownerValue': 10,
            'stakeholders': [{
                'stakeholderId': createMail(2),
                'modelValue': 5
            }, {
                'stakeholderId': createMail(3),
                'modelValue': 5
            }]
        }]

        new_reports = engine._process_reports(reports)

        assert new_reports == {'EUR': {'user2@email.com': [(5, 1)]}}
        payout_engine.ReportSemiPaid.objects.get.assert_has_calls([call(report=1)])
        payout_engine.User.objects.get.assert_has_calls([call(username=createMail(1)), call(username=createMail(2))])

    def test_process_payouts_create_lock(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.get_database_connection().wstore_payout.find_one_and_update.side_effect = [None, MagicMock(), None]
        payout_engine.Context.objects.all()[0].payouts_n = 10

        data = {}
        engine._process_payouts(data)

        assert payout_engine.Context.objects.all()[0].payouts_n == 10

        payout_engine.get_database_connection().wstore_payout.insert_one.assert_called_once_with({'_id': self.reference, '_lock': False})

        payout_engine.get_database_connection().wstore_payout.find_one_and_update.assert_has_calls([
            call({'_id': self.reference},
                 {'$set': {'_lock': True}}),
            call({'_id': self.reference},
                 {'$set': {'_lock': True}}),
            call({'_id': self.reference},
                 {'$set': {'_lock': False}})])

    def test_process_payouts_raise_in_lock(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.get_database_connection().wstore_payout.find_one_and_update.return_value = {'_lock': True}
        payout_engine.Context.objects.all()[0].payouts_n = 10

        data = {}

        with self.assertRaisesMessage(PayoutError, 'There is a payout running.'):
            engine._process_payouts(data)

        assert payout_engine.Context.objects.all()[0].payouts_n == 10

        payout_engine.get_database_connection().wstore_payout.insert_one.assert_not_called()

        payout_engine.get_database_connection().wstore_payout.find_one_and_update.assert_has_calls([
            call({'_id': self.reference},
                 {'$set': {'_lock': True}})])

    def test_process_payouts_single_payout(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.Context.objects.all()[0].payouts_n = 10

        data = {'EUR': {'user1@email.com': [(10, 1)]}}

        result = engine._process_payouts(data)

        assert len(result) == 1
        engine.paypal.batch_payout.assert_called_once_with([{'amount': {'currency': 'EUR', 'value': '10.00'}, 'sender_item_id': '1_10', 'recipient_type': 'EMAIL', 'receiver': createMail(1)}])

        assert payout_engine.Context.objects.all()[0].payouts_n == 11

        payout_engine.get_database_connection().wstore_payout.insert_one.assert_not_called()
        assert payout_engine.get_database_connection().wstore_payout.find_one_and_update.call_args_list == [
            call({'_id': self.reference},
                 {'$set': {'_lock': True}}),
            call({'_id': self.reference},
                 {'$set': {'_lock': False}})]

    def test_process_payouts_multiple_currencies_payouts(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.Context.objects.all()[0].payouts_n = 10

        data = {'EUR': {'user1@email.com': [(10, 1)]}, 'USD': {'user2@email.com': [(20, 2)]}}

        result = engine._process_payouts(data)

        assert len(result) == 2
        expected_usd = [{'amount': {'currency': 'USD', 'value': '20.00'}, 'sender_item_id': '2_10', 'recipient_type': 'EMAIL', 'receiver': createMail(2)}]
        expected_eur = [{'amount': {'currency': 'EUR', 'value': '10.00'}, 'sender_item_id': '1_11', 'recipient_type': 'EMAIL', 'receiver': createMail(1)}]
        engine.paypal.batch_payout.assert_has_calls([call(expected_usd), call(expected_eur)])

        assert payout_engine.Context.objects.all()[0].payouts_n == 12

        payout_engine.get_database_connection().wstore_payout.insert_one.assert_not_called()
        assert payout_engine.get_database_connection().wstore_payout.find_one_and_update.call_args_list == [
            call({'_id': self.reference},
                 {'$set': {'_lock': True}}),
            call({'_id': self.reference},
                 {'$set': {'_lock': False}})]

    def test_process_payouts_multiple_payouts(self):
        engine = payout_engine.PayoutEngine()
        payout_engine.Context.objects.all()[0].payouts_n = 10

        data = {'EUR': {'user1@email.com': [(10, 1), (4, 2)], 'user2@email.com': [(2.21, 1), (20, 2)], 'user3@email.com': [(4, 1)]}}

        result = engine._process_payouts(data)

        assert len(result) == 1

        expected = [
            {'amount': {'currency': 'EUR', 'value': '10.00'}, 'sender_item_id': '1_10', 'recipient_type': 'EMAIL', 'receiver': createMail(1)},
            {'amount': {'currency': 'EUR', 'value': '4.00'}, 'sender_item_id': '2_11', 'recipient_type': 'EMAIL', 'receiver': createMail(1)},
            {'amount': {'currency': 'EUR', 'value': '2.21'}, 'sender_item_id': '1_12', 'recipient_type': 'EMAIL', 'receiver': createMail(2)},
            {'amount': {'currency': 'EUR', 'value': '20.00'}, 'sender_item_id': '2_13', 'recipient_type': 'EMAIL', 'receiver': createMail(2)},
            {'amount': {'currency': 'EUR', 'value': '4.00'}, 'sender_item_id': '1_14', 'recipient_type': 'EMAIL', 'receiver': createMail(3)}
        ]
        engine.paypal.batch_payout.assert_called_once_with(expected)

        assert payout_engine.Context.objects.all()[0].payouts_n == 15

        payout_engine.get_database_connection().wstore_payout.insert_one.assert_not_called()
        assert payout_engine.get_database_connection().wstore_payout.find_one_and_update.call_args_list == [
            call({'_id': self.reference},
                 {'$set': {'_lock': True}}),
            call({'_id': self.reference},
                 {'$set': {'_lock': False}})]

    def test_process_reports_empty(self):
        engine = payout_engine.PayoutEngine()
        engine._process_reports = MagicMock(return_value="returned")
        engine._process_payouts = MagicMock(return_value=[])
        engine.process_reports([])

        engine._process_reports.assert_called_once_with([])
        engine._process_payouts.assert_called_once_with('returned')
        payout_engine.ReportsPayout.assert_not_called()
        payout_engine.PayoutWatcher.assert_not_called()

    def test_process_reports_single_payout(self):
        engine = payout_engine.PayoutEngine()
        engine._process_reports = MagicMock()
        payout1 = {
            'batch_header': {
                'payout_batch_id': 'payoutId',
                'batch_status': 'SUCCESS'
            }
        }
        payouts = [(payout1, True)]
        engine._process_payouts = MagicMock(return_value=payouts)
        rpayout = ReportsPayout(['report1'], 'payoutId', 'SUCCESS', MagicMock())
        payout_engine.ReportsPayout.return_value = rpayout
        engine.process_reports(['report1'])

        payout_engine.ReportsPayout.assert_called_once_with(reports=['report1'], payout_id='payoutId', status='SUCCESS')
        rpayout.save.assert_called_once_with()
        payout_engine.PayoutWatcher.assert_called_once_with([payout1], ['report1'])

    def test_process_reports_complex(self):
        engine = payout_engine.PayoutEngine()
        engine._process_reports = MagicMock()
        payout = {
            'batch_header': {
                'payout_batch_id': 'payoutId',
                'batch_status': 'SUCCESS'
            }
        }
        err_payout = {
            'sender_batch_header': {
                'sender_batch_id': 'BATCHID'
            }
        }
        payouts = [(payout.copy(), True), (err_payout.copy(), False), (payout.copy(), True)]
        engine._process_payouts = MagicMock(return_value=payouts)
        rpayout = ReportsPayout(['report1'], 'payoutId', 'SUCCESS', MagicMock())
        payout_engine.ReportsPayout.return_value = rpayout
        engine.process_reports(['report1'])

        payout_engine.ReportsPayout.assert_has_calls([call(reports=['report1'], payout_id='payoutId', status='SUCCESS'), call(reports=['report1'], payout_id='payoutId', status='SUCCESS')])
        rpayout.save.assert_has_calls([call(), call()])
        payout_engine.PayoutWatcher.assert_called_once_with([payout.copy(), payout.copy()], ['report1'])

    def test_process_unpaid(self):
        # Process unpaid just ask for unpaids and process them
        engine = payout_engine.PayoutEngine()
        engine._get_reports = MagicMock(return_value=[1, 2, 3])
        engine.process_reports = MagicMock()

        engine.process_unpaid()

        engine._get_reports.assert_called_once_with()
        engine.process_reports.assert_called_once_with([1, 2, 3])
