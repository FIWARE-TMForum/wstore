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

from bson import ObjectId
from mock import MagicMock, call, ANY
from nose_parameterized import parameterized

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from wstore.management.commands import loadplugin, removeplugin, resend_upgrade


class FakeCommandError(Exception):
    pass


class PluginManagementTestCase(TestCase):

    tags = ('management',)

    def _install_plugin_error(self):
        self.loader_mock.install_plugin.side_effect = Exception('Error installing plugin')

    def _unistall_plugin_error(self):
        self.loader_mock.uninstall_plugin.side_effect = Exception('Error uninstalling plugin')

    def _check_loaded(self):
        self.loader_mock.install_plugin.assert_called_once_with('test_plugin.zip')

    def _check_removed(self):
        self.loader_mock.uninstall_plugin.assert_called_once_with('test_plugin')

    def _test_plugin_command(self, module, module_name, args, checker=None, side_effect=None, err_msg=None):
        # Create Mocks
        module.stout = MagicMock()
        module.CommandError = FakeCommandError
        module.PluginLoader = MagicMock(name="PluginLoader")

        self.loader_mock = MagicMock()
        module.PluginLoader.return_value = self.loader_mock

        if side_effect is not None:
            side_effect(self)

        opts = {}
        error = None
        try:
            call_command(module_name, *args, **opts)
        except Exception as e:
            error = e

        if err_msg is None:
            self.assertEquals(error, None)
            checker(self)
        else:
            self.assertTrue(isinstance(error, FakeCommandError))
            self.assertEquals(unicode(e), err_msg)

    @parameterized.expand([
        ('correct', ['test_plugin.zip'], _check_loaded),
        ('inv_argument', ['test1', 'test2'], None,  None, "Error: Please specify the path to the plugin package"),
        ('exception', ['test_plugin.zip'], None, _install_plugin_error, 'Error installing plugin')
    ])
    def test_load_plugin(self, name, args, checker=None, side_effect=None, err_msg=None):
        self._test_plugin_command(loadplugin, 'loadplugin', args, checker, side_effect, err_msg)

    @parameterized.expand([
        ('correct', ['test_plugin'], _check_removed),
        ('inv_argument_mul', ['test1', 'test2'], None, None, "Error: Please specify only one plugin to be deleted"),
        ('inv_argument', [], None, None, "Error: Please specify the plugin to be deleted"),
        ('exception', ['test_plugin'], None, _unistall_plugin_error, 'Error uninstalling plugin')
    ])
    def test_remove_plugin(self, name, args, checker=None, side_effect=None, err_msg=None):
        self._test_plugin_command(removeplugin, 'removeplugin', args, checker, side_effect, err_msg)


class ResendUpgradeTestCase(TestCase):
    tags = ('management', 'upgrades')

    _ctx_pk = '58a447608e05ac5752d96d98'

    def setUp(self):
        # Mock context
        self._ctx_inst = MagicMock(pk=self._ctx_pk)
        resend_upgrade.Context = MagicMock()
        resend_upgrade.Context.objects.all.return_value = [self._ctx_inst]
        resend_upgrade.Context.objects.get.return_value = self._ctx_inst

        # Mock db connection
        self._lock_inst = MagicMock()
        resend_upgrade.DocumentLock = MagicMock(return_value=self._lock_inst)

        self._upg_inst = MagicMock()
        resend_upgrade.InventoryUpgrader = MagicMock(return_value=self._upg_inst)

        resend_upgrade.Resource = MagicMock()

    def _check_context_calls(self):
        resend_upgrade.Context.objects.all.assert_called_once_with()
        resend_upgrade.Context.objects.get.assert_called_once_with(pk=self._ctx_pk)
        self._ctx_inst.save.assert_called_once_with()

    def test_resend_upgrades_no_pending_unlocked(self):
        self._ctx_inst.failed_upgrades = []

        call_command('resend_upgrade')

        self._check_context_calls()

        self.assertEquals(0, resend_upgrade.InventoryUpgrader.call_count)

        resend_upgrade.DocumentLock.assert_called_once_with('wstore_context', self._ctx_pk, 'ctx')
        self._lock_inst.wait_document.assert_called_once_with()
        self._lock_inst.unlock_document.assert_called_once_with()

    def test_resend_upgrades_pending_locked(self):
        self._ctx_inst.failed_upgrades = [{
            'asset_id': '1',
            'pending_offerings': ['1'],
            'pending_products': []
        }, {
            'asset_id': '2',
            'pending_offerings': [],
            'pending_products': ['1', '2', '3']
        }]

        asset1 = MagicMock(pk='1')
        asset2 = MagicMock(pk='2')

        resend_upgrade.Resource.objects.get.side_effect = [asset1, asset2]

        self._upg_inst.upgrade_asset_products.return_value = [], []

        self._passed_method = None

        def upgrade_mock(prod, method):
            self._passed_method = method
            return ['2']

        self._upg_inst.upgrade_products.side_effect = upgrade_mock

        call_command('resend_upgrade')

        self._check_context_calls()
        self.assertEquals([{
            'asset_id': '2',
            'pending_offerings': [],
            'pending_products': ['2']
        }], self._ctx_inst.failed_upgrades)

        self.assertEquals([
            call(pk='1'),
            call(pk='2')
        ], resend_upgrade.Resource.objects.get.call_args_list)

        self.assertEquals([
            call(asset1),
            call(asset2)
        ], resend_upgrade.InventoryUpgrader.call_args_list)

        self._upg_inst.upgrade_asset_products.assert_called_once_with(['1'])
        self._upg_inst.upgrade_products.assert_called_once_with(['1', '2', '3'], ANY)

        # Validate that the lambda method passed to the upgrader is working properly
        self.assertEquals('1', self._passed_method('1'))

        resend_upgrade.DocumentLock.assert_called_once_with('wstore_context', self._ctx_pk, 'ctx')
        self._lock_inst.wait_document.assert_called_once_with()
        self._lock_inst.unlock_document.assert_called_once_with()

    def test_pending_upgrades_no_context(self):
        resend_upgrade.Context.objects.all.return_value = []

        try:
            call_command('resend_upgrade')
        except CommandError as e:
            msg = unicode(e)

        self.assertEquals('Context object is not yet created', msg)
