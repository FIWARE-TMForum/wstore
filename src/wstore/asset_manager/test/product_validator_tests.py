# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid
# Copyright (c) 2021 Future Internet Consulting and Development Solutions S.L.

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


from importlib import reload

from bson import ObjectId
from django.core.exceptions import PermissionDenied
from django.test.testcases import TestCase
from mock import MagicMock, call
from parameterized import parameterized

from wstore.asset_manager import offering_validator, product_validator
from wstore.asset_manager.errors import ProductError
from wstore.asset_manager.test.product_validator_test_data import *
from wstore.store_commons.errors import ConflictError


class ValidatorTestCase(TestCase):
    tags = ("product-validator",)

    def _mock_validator_imports(self, module):
        reload(module)

        module.ResourcePlugin = MagicMock()
        module.ResourcePlugin.objects.get.return_value = self._plugin_instance

        module.Resource = MagicMock()
        self._asset_instance = MagicMock()
        self._asset_instance.resource_type = "Widget"
        self._asset_instance.content_type = "application/x-widget"
        self._asset_instance.provider = self._provider
        self._asset_instance.product_id = None
        self._asset_instance.is_public = False
        self._asset_instance.pk = ObjectId("61004aba5e05acc115f022f0")

        module.Resource.objects.filter.return_value = [self._asset_instance]
        module.Resource.objects.get.return_value = self._asset_instance
        module.Resource.objects.create.return_value = self._asset_instance

    def setUp(self):
        self._provider = MagicMock()

        self._plugin_instance = MagicMock()
        self._plugin_instance.media_types = ["application/x-widget"]
        self._plugin_instance.formats = ["FILE"]
        self._plugin_instance.module = "wstore.asset_manager.resource_plugins.plugin.Plugin"
        self._plugin_instance.form = {}

        import wstore.asset_manager.resource_plugins.decorators

        wstore.asset_manager.resource_plugins.decorators.ResourcePlugin = MagicMock()
        wstore.asset_manager.resource_plugins.decorators.ResourcePlugin.objects.get.return_value = self._plugin_instance

        # Mock Site
        product_validator.settings.SITE = "http://testlocation.org/"

    def tearDown(self):
        reload(offering_validator)
        reload(product_validator)

    def _not_existing(self):
        self._plugin_instance.formats = ["FILE", "URL"]
        product_validator.Resource.objects.filter.return_value = []

    def _not_supported(self):
        import wstore.asset_manager.resource_plugins.decorators

        wstore.asset_manager.resource_plugins.decorators.ResourcePlugin.objects.get.side_effect = Exception("Not found")
        self._mock_validator_imports(product_validator)

    def _inv_media(self):
        product_validator.Resource.objects.filter.return_value = []
        self._plugin_instance.media_types = ["text/plain"]
        self._plugin_instance.formats = ["URL"]

    def _not_owner(self):
        self._asset_instance.provider = MagicMock()

    def _diff_media(self):
        self._asset_instance.content_type = "text/plain"

    def _existing_asset(self):
        self._asset_instance.product_id = 27

    def _invalid_type(self):
        self._asset_instance.resource_type = "Mashup"

    def _metadata_plugin(self):
        self._plugin_instance.form = {"data": "data"}
        self._plugin_instance.formats = ["URL"]
        product_validator.Resource.objects.filter.return_value = []

    def _pub_asset(self):
        self._asset_instance.is_public = True

    def test_validate_creation_registered_file(self):
        self._mock_validator_imports(product_validator)

        validator = product_validator.ProductValidator()
        validator.validate("create", self._provider, BASIC_PRODUCT["product"])

        product_validator.ResourcePlugin.objects.get.assert_called_once_with(name="Widget")
        product_validator.Resource.objects.filter.assert_called_once_with(download_link=PRODUCT_LOCATION)
        self.assertFalse(product_validator.Resource.objects.get().has_terms)
        product_validator.Resource.objects.get().save.assert_called_once_with()

    def test_validate_creation_new_url(self):
        self._mock_validator_imports(product_validator)
        product_validator.Resource.objects.filter.return_value = []
        self._plugin_instance.formats = ["URL"]

        validator = product_validator.ProductValidator()
        validator.validate("create", self._provider, TERMS_PRODUCT["product"])

        product_validator.Resource.objects.create.assert_called_once_with(
            has_terms=True,
            resource_path="",
            download_link=PRODUCT_LOCATION,
            provider=self._provider,
            content_type="application/x-widget",
        )

    def _attached(self):
        self._asset_instance.state = "attached"

    def _inv_product_id(self):
        self._asset_instance.state = "upgrading"
        self._asset_instance.product_id = "10"

    def _set_asset_params(self):
        self._asset_instance.state = "upgrading"
        self._asset_instance.product_id = UPGRADE_PRODUCT["product"]["id"]

    def _high_asset_version(self):
        self._set_asset_params()
        self._asset_instance.old_versions = [MagicMock(version="3.0")]
        self._asset_instance.resource_path = ""

    @parameterized.expand(
        [
            (
                "invalid_action",
                INVALID_ACTION,
                None,
                ValueError,
                "The provided action (invalid) is not valid. Allowed values are create, attach, update, upgrade, and delete",
            ),
            (
                "missing_media",
                MISSING_MEDIA,
                None,
                ProductError,
                "ProductError: Digital product specifications must contain a media type characteristic",
            ),
            (
                "missing_type",
                MISSING_TYPE,
                None,
                ProductError,
                "ProductError: Digital product specifications must contain a asset type characteristic",
            ),
            (
                "missing_location",
                MISSING_LOCATION,
                None,
                ProductError,
                "ProductError: Digital product specifications must contain a location characteristic",
            ),
            (
                "missing_asset_id",
                MISSING_ASSET_ID,
                None,
                ProductError,
                "ProductError: Digital product specifications must contain a asset characteristic",
            ),
            (
                "multiple_license",
                MULTIPLE_TERMS,
                None,
                ProductError,
                "ProductError: The product specification must not contain more than one license characteristic",
            ),
            (
                "multiple_char",
                MULTIPLE_LOCATION,
                None,
                ProductError,
                "ProductError: The product specification must not contain more than one location characteristic",
            ),
            (
                "multiple_values",
                MULTIPLE_VALUES,
                None,
                ProductError,
                "ProductError: The characteristic Location must not contain multiple values",
            ),
            (
                "inv_location",
                INVALID_LOCATION,
                None,
                ProductError,
                "ProductError: The location characteristic included in the product specification is not a valid URL",
            ),
            (
                "unauthorized",
                BASIC_PRODUCT,
                _not_owner,
                PermissionDenied,
                "You are not authorized to use the digital asset specified in the location characteristic",
            ),
            (
                "existing_asset",
                BASIC_PRODUCT,
                _existing_asset,
                ConflictError,
                "There is already an existing product specification defined for the given digital asset",
            ),
            (
                "invalid_asset_type",
                BASIC_PRODUCT,
                _invalid_type,
                ProductError,
                "ProductError: The specified asset type is different from the asset one",
            ),
            (
                "diff_media",
                BASIC_PRODUCT,
                _diff_media,
                ProductError,
                "ProductError: The provided media type characteristic is different from the asset one",
            ),
            (
                "not_asset",
                BASIC_PRODUCT,
                _not_existing,
                ProductError,
                "ProductError: The URL specified in the location characteristic does not point to a valid digital asset",
            ),
            (
                "exp_metadata",
                TERMS_PRODUCT,
                _metadata_plugin,
                ProductError,
                "ProductError: Automatic creation of digital assets with expected metadata is not supported",
            ),
            (
                "inv_media",
                BASIC_PRODUCT,
                _inv_media,
                ProductError,
                "ProductError: The media type characteristic included in the product specification is not valid for the given asset type",
            ),
            (
                "public_asset",
                BASIC_PRODUCT,
                _pub_asset,
                ProductError,
                "ProductError: It is not allowed to create products with public assets",
            ),
            (
                "upgrade_asset_not_found",
                UPGRADE_PRODUCT,
                _not_existing,
                ProductError,
                "ProductError: The URL specified in the location characteristic does not point to a valid digital asset",
            ),
            (
                "upgrade_attached_asset",
                UPGRADE_PRODUCT,
                _attached,
                ProductError,
                "ProductError: There is not a new version of the specified digital asset",
            ),
            (
                "upgrade_invalid_product_id",
                UPGRADE_PRODUCT,
                _inv_product_id,
                ProductError,
                "ProductError: The specified digital asset is included in other product spec",
            ),
            (
                "upgrade_asset_inv_version",
                UPGRADE_PRODUCT_INV_VERSION,
                _set_asset_params,
                ProductError,
                "ProductError: The field version does not have a valid format",
            ),
            (
                "upgrade_low_version",
                UPGRADE_PRODUCT,
                _high_asset_version,
                ProductError,
                "ProductError: The provided version is not higher that the previous one",
            ),
        ]
    )
    def test_validate_error(self, name, data, side_effect, err_type, err_msg):
        self._mock_validator_imports(product_validator)
        self._mock_document_lock()

        if side_effect is not None:
            side_effect(self)

        error = None
        try:
            validator = product_validator.ProductValidator()
            validator.validate(data["action"], self._provider, data["product"])
        except Exception as e:
            error = e

        self.assertTrue(isinstance(error, err_type))
        self.assertEquals(err_msg, str(error))

    def _mock_upgrading_asset(self, version):
        self._asset_instance.state = "upgrading"
        self._asset_instance.product_id = UPGRADE_PRODUCT["product"]["id"]
        self._asset_instance.version = version
        self._asset_instance.old_versions = [MagicMock(version="1.0")]

    def _mock_document_lock(self):
        document_lock = MagicMock()
        product_validator.DocumentLock = MagicMock(return_value=document_lock)

        return document_lock

    def test_validate_upgrade(self):
        self._mock_validator_imports(product_validator)
        self._mock_upgrading_asset("")

        doc_lock = self._mock_document_lock()

        validator = product_validator.ProductValidator()
        validator.validate("upgrade", self._provider, UPGRADE_PRODUCT["product"])

        self.assertEquals(UPGRADE_PRODUCT["product"]["version"], self._asset_instance.version)
        self.assertEquals("upgrading", self._asset_instance.state)
        self._asset_instance.save.assert_called_once_with()

        product_validator.DocumentLock.assert_called_once_with("wstore_resource", self._asset_instance.pk, "asset")
        doc_lock.wait_document.assert_called_once_with()
        doc_lock.unlock_document.assert_called_once_with()

    def test_attach_upgrade(self):
        self._mock_validator_imports(product_validator)
        self._mock_upgrading_asset(UPGRADE_PRODUCT["product"]["version"])

        doc_lock = self._mock_document_lock()

        # Mock inventory upgrader class
        product_validator.InventoryUpgrader = MagicMock()

        validator = product_validator.ProductValidator()
        validator.validate("attach_upgrade", self._provider, UPGRADE_PRODUCT["product"])

        self.assertEquals("attached", self._asset_instance.state)

        product_validator.InventoryUpgrader.assert_called_once_with(self._asset_instance)
        product_validator.InventoryUpgrader().start.assert_called_once_with()

        self._asset_instance.save.assert_called_once_with()

        product_validator.DocumentLock.assert_called_once_with("wstore_resource", self._asset_instance.pk, "asset")
        doc_lock.wait_document.assert_called_once_with()
        doc_lock.unlock_document.assert_called_once_with()

    def test_attach_upgrade_non_digital(self):
        self._mock_validator_imports(product_validator)

        validator = product_validator.ProductValidator()
        validator.validate(
            "attach_upgrade",
            self._provider,
            {"version": "1.0", "productSpecCharacteristic": []},
        )

        # The method did nothing
        self.assertEquals(0, product_validator.ResourcePlugin.objects.get.call_count)

    @parameterized.expand(
        [
            ("missing_version", {}),
            ("missing_charact", {"version": "1.0"}),
            ("non_digital", {"version": "1.0", "productSpecCharacteristic": []}),
        ]
    )
    def test_validate_upgrade_missing_info(self, name, data):
        self._mock_validator_imports(product_validator)
        self._asset_instance.state = "upgrading"

        validator = product_validator.ProductValidator()
        validator.validate("upgrade", self._provider, data)

        self.assertEquals("upgrading", self._asset_instance.state)

    def _non_digital(self):
        return [[], []]

    def _mixed_assets(self):
        digital_asset = MagicMock(pk="1")
        product_validator.Resource.objects.filter.side_effect = [[], [digital_asset]]

    def _all_digital(self):
        digital_asset = MagicMock(pk="1")
        digital_asset1 = MagicMock(pk="2")
        return [[digital_asset], [digital_asset1]]

    @parameterized.expand([("non_digital", _non_digital, False), ("all_digital", _all_digital)])
    def test_bundle_creation(self, name, asset_mocker, created=True):
        self._mock_validator_imports(product_validator)

        assets = asset_mocker(self)
        expected_assets = [asset[0].pk for asset in assets if len(asset)]

        product_validator.Resource.objects.filter.side_effect = assets

        validator = product_validator.ProductValidator()
        validator.validate(
            BASIC_BUNDLE_CREATION["action"],
            self._provider,
            BASIC_BUNDLE_CREATION["product"],
        )

        # Validate filter calls
        self.assertEquals(
            [
                call(product_id=BASIC_BUNDLE_CREATION["product"]["bundledProductSpecification"][0]["id"]),
                call(product_id=BASIC_BUNDLE_CREATION["product"]["bundledProductSpecification"][1]["id"]),
            ],
            product_validator.Resource.objects.filter.call_args_list,
        )

        # Check resource creation
        if created:
            product_validator.Resource.objects.create.assert_called_once_with(
                has_terms=False,
                resource_path="",
                download_link="",
                provider=self._provider,
                content_type="bundle",
                bundled_assets=expected_assets,
            )
        else:
            self.assertEquals(0, product_validator.Resource.objects.call_count)

    def _validate_bundle_creation_error(self, product_request, msg, side_effect=None):
        self._mock_validator_imports(product_validator)

        if side_effect is not None:
            side_effect()

        try:
            validator = product_validator.ProductValidator()
            validator.validate(product_request["action"], self._provider, product_request["product"])
        except ProductError as e:
            error = e

        self.assertEquals(msg, str(error))

    def test_bundle_creation_missing_products(self):
        self._validate_bundle_creation_error(
            {"action": "create", "product": {"isBundle": True}},
            "ProductError: A product spec bundle must contain at least two bundled product specs",
        )

    def test_bundle_creation_mixed_content(self):
        self._validate_bundle_creation_error(
            BASIC_BUNDLE_CREATION,
            "ProductError: Mixed product bundles are not allowed. All bundled products must be digital or physical",
            self._mixed_assets,
        )

    def test_bundle_assets_included(self):
        product_request = deepcopy(BASIC_PRODUCT)
        product_request["product"]["isBundle"] = True

        self._validate_bundle_creation_error(
            product_request,
            "ProductError: Product spec bundles cannot define digital assets",
        )

    def _non_pending_bundles(self):
        product_validator.Resource.objects.filter.return_value = []

    def _pending_bundles(self):
        product1 = MagicMock(product_id="1", pk="1a")
        product2 = MagicMock(product_id="2", pk="2a")

        bundle1 = MagicMock()
        bundle1.bundled_assets = [{}]

        bundle2 = MagicMock()
        bundle2.bundled_assets = ["2a", "3a"]

        self._asset_instance.bundled_assets = ["1a", "2a"]

        product_validator.Resource.objects.filter.side_effect = [
            [bundle1, bundle2, self._asset_instance],
            [product1],
            [product2],
        ]

    @parameterized.expand(
        [
            ("digital_asset", BASIC_PRODUCT["product"], True, True),
            ("non_digital", {"isBundle": False}),
            (
                "bundle_non_pending",
                BASIC_BUNDLE_CREATION["product"],
                False,
                False,
                True,
                _non_pending_bundles,
            ),
            (
                "bundle_multiple_pending",
                BASIC_BUNDLE_CREATION["product"],
                False,
                True,
                True,
                _pending_bundles,
            ),
        ]
    )
    def test_attach_info(
        self,
        name,
        product_spec,
        is_digital=False,
        is_attached=False,
        is_bundle=False,
        filter_mock=None,
    ):
        self._mock_validator_imports(product_validator)

        if filter_mock is not None:
            filter_mock(self)

        validator = product_validator.ProductValidator()

        digital_chars = (
            ("type", "media", "http://location", "61004aba5e05acc115f022f0") if is_digital else (None, None, None, None)
        )
        validator.parse_characteristics = MagicMock(return_value=digital_chars)

        validator.validate("attach", self._provider, product_spec)

        # Check calls
        validator.parse_characteristics.assert_called_once_with(product_spec)
        if is_digital:
            product_validator.Resource.objects.get.assert_called_once_with(pk=ObjectId(digital_chars[3]))
            self.assertEquals(0, product_validator.Resource.objects.filter.call_count)

        if is_bundle:
            self.assertEquals(
                [
                    call(
                        product_id=None,
                        provider=self._provider,
                        content_type="bundle",
                        resource_path="",
                        download_link="",
                    ),
                    call(product_id="1"),
                    call(product_id="2"),
                ],
                product_validator.Resource.objects.filter.call_args_list,
            )
            self.assertEquals(0, product_validator.Resource.objects.get.call_count)

        if is_attached:
            self.assertEquals(product_spec["id"], self._asset_instance.product_id)
            self.assertEquals(product_spec["version"], self._asset_instance.version)
            self.assertEquals(digital_chars[0], self._asset_instance.resource_type)
            self.assertEquals("attached", self._asset_instance.state)

            self._asset_instance.save.assert_called_once_with()
        else:
            self.assertEquals(0, self._asset_instance.save.call_count)

    @parameterized.expand([("no_chars", NO_CHARS_PRODUCT), ("no_digital_chars", EMPTY_CHARS_PRODUCT)])
    def test_validate_physical(self, name, product):
        self._mock_validator_imports(product_validator)
        validator = product_validator.ProductValidator()
        validator.validate("create", self._provider, product)

        self.assertEquals(0, product_validator.ResourcePlugin.objects.get.call_count)
        self.assertEquals(0, product_validator.Resource.objects.get.call_count)
        self.assertEquals(0, product_validator.Resource.objects.create.call_count)

    def _validate_offering_calls(self, offering, asset, is_digital, is_open=False):
        # Check resource retrieving if needed
        offering_validator.Resource.objects.filter.assert_called_once_with(
            product_id=offering["productSpecification"]["id"]
        )

        # Check offering creation
        offering_validator.Offering.objects.create.assert_called_once_with(
            owner_organization=self._provider,
            name=offering["name"],
            description="",
            version=offering["version"],
            is_digital=is_digital,
            is_open=is_open,
            asset=asset,
            bundled_offerings=[],
        )

    def _validate_single_offering_calls(self, offering):
        self._validate_offering_calls(offering, self._asset_instance, True)

    def _validate_physical_offering_calls(self, offering):
        self._validate_offering_calls(offering, None, False)

    def _validate_bundle_offering_calls(self, offering, is_digital, is_open=False):
        self.assertEquals(
            [call(off_id=off["id"]) for off in offering["bundledProductOffering"]],
            offering_validator.Offering.objects.filter.call_args_list,
        )

        # Validate offering creation
        offering_validator.Offering.objects.create.assert_called_once_with(
            owner_organization=self._provider,
            name=offering["name"],
            description="",
            version=offering["version"],
            is_digital=is_digital,
            is_open=is_open,
            asset=None,
            bundled_offerings=[off[0].pk for off in self._bundles],
        )

    def _validate_bundle_digital_offering_calls(self, offering):
        self._validate_bundle_offering_calls(offering, True)

    def _validate_bundle_physical_offering_calls(self, offering):
        self._validate_bundle_offering_calls(offering, False)

    def _validate_open_offering_calls(self, offering):
        self._validate_offering_calls(offering, self._asset_instance, True, is_open=True)
        self.assertTrue(self._asset_instance.is_public)
        self._asset_instance.save.assert_called_once_with()

    def _validate_open_bundle_calls(self, offering):
        self._validate_bundle_offering_calls(offering, True, is_open=True)

    def _mock_product_request(self):
        offering_validator.requests = MagicMock()
        product = deepcopy(BASIC_PRODUCT["product"])
        product["id"] = "20"
        resp = MagicMock()
        offering_validator.requests.get.return_value = resp
        resp.json.return_value = product
        resp.status_code = 200

    def _mock_offering_bundle(self, offering, is_digital=True):
        offering_validator.Offering = MagicMock()

        self._bundles = (
            []
            if "bundledProductOffering" not in offering
            else [[MagicMock(id=off["id"], is_digital=is_digital)] for off in offering["bundledProductOffering"]]
        )
        offering_validator.Offering.objects.filter.side_effect = self._bundles

    def _non_digital_offering(self):
        offering_validator.Resource.objects.filter.return_value = []

    def _non_digital_bundle(self):
        self._mock_offering_bundle(BUNDLE_OFFERING, is_digital=False)

    def _invalid_bundled(self):
        offering_validator.Offering.objects.filter.side_effect = None
        offering_validator.Offering.objects.filter.return_value = []

    def _open_bundled(self):
        for bundle_resp in self._bundles:
            for bundle in bundle_resp:
                bundle.is_open = True

    def _open_existing(self):
        offering_responses = [bund for bund in self._bundles]
        offering_responses.append([MagicMock(id="6"), MagicMock(id="8")])
        offering_validator.Offering.objects.filter.side_effect = offering_responses

    def _mixed_bundled_offerings(self):
        offering_validator.Offering.objects.filter.side_effect = [
            [MagicMock(id="6", is_digital=True)],
            [MagicMock(id="7", is_digital=False)],
        ]

    def _catalog_api_error(self):
        offering_validator.requests.get().status_code = 500

    def _non_open_bundled(self):
        for bundle_resp in self._bundles:
            for bundle in bundle_resp:
                bundle.is_open = False

    @parameterized.expand(
        [
            ("valid_pricing", BASIC_OFFERING, _validate_single_offering_calls, None),
            (
                "zero_offering",
                ZERO_OFFERING,
                None,
                None,
                "Invalid price, it must be greater than zero.",
            ),
            (
                "free_offering",
                FREE_OFFERING,
                _validate_physical_offering_calls,
                _non_digital_offering,
            ),
            (
                "bundle_offering",
                BUNDLE_OFFERING,
                _validate_bundle_digital_offering_calls,
                None,
            ),
            (
                "bundle_offering_non_digital",
                BUNDLE_OFFERING,
                _validate_bundle_physical_offering_calls,
                _non_digital_bundle,
            ),
            ("open_offering", OPEN_OFFERING, _validate_open_offering_calls, None),
            ("open_bundle", OPEN_BUNDLE, _validate_open_bundle_calls, _open_bundled),
            (
                "missing_type",
                MISSING_PRICETYPE,
                None,
                None,
                "Missing required field priceType in productOfferingPrice",
            ),
            (
                "invalid_type",
                INVALID_PRICETYPE,
                None,
                None,
                "Invalid priceType, it must be one time, recurring, or usage",
            ),
            (
                "missing_charge_period",
                MISSING_PERIOD,
                None,
                None,
                "Missing required field recurringChargePeriod for recurring priceType",
            ),
            (
                "invalid_period",
                INVALID_PERIOD,
                None,
                None,
                "Unrecognized recurringChargePeriod: invalid",
            ),
            (
                "missing_price",
                MISSING_PRICE,
                None,
                None,
                "Missing required field price in productOfferingPrice",
            ),
            (
                "missing_currency",
                MISSING_CURRENCY,
                None,
                None,
                "Missing currency code in price",
            ),
            (
                "invalid_currency",
                INVALID_CURRENCY,
                None,
                None,
                "Unrecognized currency: invalid",
            ),
            (
                "missing_name",
                MISSING_NAME,
                None,
                None,
                "Missing required field name in productOfferingPrice",
            ),
            (
                "multiple_names",
                MULTIPLE_NAMES,
                None,
                None,
                "Price plans names must be unique (Plan)",
            ),
            (
                "bundle_missing",
                BUNDLE_MISSING_FIELD,
                None,
                None,
                "Offering bundles must contain a bundledProductOffering field",
            ),
            (
                "bundle_invalid_number",
                BUNDLE_MISSING_ELEMS,
                None,
                None,
                "Offering bundles must contain at least two bundled offerings",
            ),
            (
                "bundle_inv_bundled",
                BUNDLE_OFFERING,
                None,
                _invalid_bundled,
                "The bundled offering 6 is not registered",
            ),
            (
                "bundle_mixed",
                BUNDLE_OFFERING,
                None,
                _mixed_bundled_offerings,
                "Mixed bundle offerings are not allowed. All bundled offerings must be digital or physical",
            ),
            (
                "open_mixed",
                OPEN_MIXED,
                None,
                None,
                "Open offerings cannot include price plans",
            ),
            (
                "open_multiple_offers",
                OPEN_OFFERING,
                None,
                _open_existing,
                "Assets of open offerings cannot be monetized in other offerings",
            ),
            (
                "open_non_digital",
                OPEN_OFFERING,
                None,
                _non_digital_offering,
                "Non digital products cannot be open",
            ),
            (
                "open_bundle_mixed",
                OPEN_BUNDLE,
                None,
                _non_open_bundled,
                "If a bundle is open all the bundled offerings must be open",
            ),
        ]
    )
    def test_create_offering_validation(self, name, offering, checker, side_effect, msg=None):
        self._mock_validator_imports(offering_validator)
        offering_validator.Resource.objects.filter.return_value = [self._asset_instance]

        self._mock_product_request()
        self._mock_offering_bundle(offering)

        # Add the extra call for open search
        offering_responses = [bund for bund in self._bundles]
        offering_responses.append([])
        offering_validator.Offering.objects.filter.side_effect = offering_responses

        if side_effect is not None:
            side_effect(self)

        error = None
        try:
            validator = offering_validator.OfferingValidator()
            validator.validate("create", self._provider, offering)
        except Exception as e:
            error = e

        if msg is not None:
            self.assertTrue(isinstance(error, ValueError))
            self.assertEquals(msg, str(error))
        else:
            self.assertEquals(error, None)

            # Validate calls
            checker(self, offering)

    def test_offering_attachment(self):
        offering = MagicMock()
        offering_validator.Offering = MagicMock()
        offering_validator.Offering.objects.filter.return_value = [offering]

        validator = offering_validator.OfferingValidator()
        validator.validate("attach", self._provider, BASIC_OFFERING)

        self.assertEquals(BASIC_OFFERING["href"], offering.href)
        self.assertEquals(BASIC_OFFERING["id"], offering.off_id)

        offering.save.assert_called_once_with()

    def test_offering_attachment_missing(self):
        offering_validator.Offering = MagicMock()
        offering_validator.Offering.objects.filter.return_value = []

        error = None
        try:
            validator = offering_validator.OfferingValidator()
            validator.validate("attach", self._provider, BASIC_OFFERING)
        except ValueError as e:
            error = e

        self.assertEquals("The specified offering has not been registered", str(error))

    def _mock_non_attached(self):
        self._asset_instance.product_id = None

    def _mock_non_upgraded(self):
        self._asset_instance.product_id = BASIC_PRODUCT["product"]["id"]
        self._asset_instance.state = "upgrading"
        self._asset_instance.resource_path = ""
        self._asset_instance.old_versions = [
            MagicMock(
                version="1.0",
                content_type="type",
                resource_path="/old/path",
                download_link="http://host/old/path",
            )
        ]

    def _mock_attached(self):
        self._asset_instance.product_id = BASIC_PRODUCT["product"]["id"]

    def _mock_wrong_product(self):
        self._asset_instance.product_id = "10"
        self._asset_instance.resource_path = "/new/path"

    def _validate_non_attached(self):
        self._asset_instance.delete.assert_called_once_with()

    def _validate_non_upgraded(self):
        self.assertEquals("1.0", self._asset_instance.version)
        self.assertEquals("type", self._asset_instance.content_type)
        self.assertEquals("/old/path", self._asset_instance.resource_path)
        self.assertEquals("http://host/old/path", self._asset_instance.download_link)
        self._asset_instance.save.assert_called_once_with()

    def _validate_not_called(self):
        self.assertEquals(0, self._asset_instance.delete.call_count)

    def _validate_non_downgraded(self):
        self.assertEquals("/new/path", self._asset_instance.resource_path)

    @parameterized.expand(
        [
            (
                "create_non_att",
                "rollback_create",
                BASIC_PRODUCT["product"],
                _mock_non_attached,
                _validate_non_attached,
            ),
            (
                "upgrade_saved",
                "rollback_upgrade",
                BASIC_PRODUCT["product"],
                _mock_non_upgraded,
                _validate_non_upgraded,
            ),
            ("create_non_dig", "rollback_create", {}, None, _validate_not_called),
            (
                "create_attached",
                "rollback_create",
                BASIC_PRODUCT["product"],
                _mock_attached,
                _validate_not_called,
            ),
            (
                "upgrade_wrong_id",
                "rollback_upgrade",
                BASIC_PRODUCT["product"],
                _mock_wrong_product,
                _validate_non_downgraded,
            ),
        ]
    )
    def test_rollback_handler(self, name, action, data, mocker, test_validator):
        self._mock_validator_imports(product_validator)

        if mocker is not None:
            mocker(self)

        validator = product_validator.ProductValidator()
        validator.validate(action, self._provider, data)

        test_validator(self)

    def _mock_offering_update(self):
        self._mock_validator_imports(offering_validator)
        offering_validator.Resource.objects.filter.return_value = [self._asset_instance]

        self._mock_product_request()

        offering_validator.Offering = MagicMock()
        offering_validator.Offering.objects.filter.return_value = []

    def test_update_offering_validator(self):
        self._mock_offering_update()

        validator = offering_validator.OfferingValidator()
        validator.validate("update", self._provider, BASIC_OFFERING)

        # Validate calls
        self.assertEquals(0, offering_validator.Offering.objects.filter.call_count)
        self.assertFalse(self._asset_instance.is_public)
        self._asset_instance.save.assert_called_once_with()

    def test_update_open_offering(self):
        self._mock_offering_update()

        validator = offering_validator.OfferingValidator()
        validator.validate("update", self._provider, OPEN_OFFERING)

        # Validate calls
        offering_validator.Offering.objects.filter.assert_called_once_with(asset=self._asset_instance)
        self.assertTrue(self._asset_instance.is_public)
        self._asset_instance.save.assert_called_once_with()

    def test_update_open_offering_multiple_error(self):
        self._mock_offering_update()

        offering_validator.Offering.objects.filter.return_value = [
            MagicMock(),
            MagicMock(),
        ]
        error = None
        try:
            validator = offering_validator.OfferingValidator()
            validator.validate("update", self._provider, OPEN_OFFERING)
        except Exception as e:
            error = e

        self.assertTrue(isinstance(error, ValueError))
        self.assertEqual(
            str(error),
            "Assets of open offerings cannot be monetized in other offerings",
        )
