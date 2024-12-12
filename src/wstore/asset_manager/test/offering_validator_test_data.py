# -*- coding: utf-8 -*-

# Copyright (c) 2024 Future Internet Consulting and Development Solutions S.L.

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

from copy import deepcopy


BASE_OFFERING = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [{
        "id": "urn:product-offering-price:1234",
        "href": "urn:product-offering-price:1234"
    }]
}

BASE_OFFERING_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [{
        "id": "urn:product-offering-price:1234",
        "href": "urn:product-offering-price:1234"
    }, {
        "id": "urn:product-offering-price:4567",
        "href": "urn:product-offering-price:4567"
    }]
}

OT_OFFERING_PRICE = {
    "id": "urn:product-offering-price:1234",
    "name": "plan",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "1.0"
    }
}

OPEN_OFFERING_PRICE = {
    "id": "urn:product-offering-price:1234",
    "name": "open",
    "description": "Open offering"
}

ZERO_PRICING = {
    "name": "plan",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "0"
    }
}

FREE_OFFERING = {
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
}

CUSTOM_OFFERING_PRICING = {
    "name": "The custom pricing",
    "priceType": "custom",
    "description": "Custom pricing description"
}

CUSTOM_OFFERING_PRICING_2 = {
    "name": "The custom pricing 2",
    "priceType": "custom",
    "description": "Custom pricing description"
}


CUSTOM_PRICING_OFFERING_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "The custom pricing",
            "priceType": "custom",
            "description": "Custom pricing description"
        },
        {
            "name": "The custom pricing 2",
            "priceType": "custom",
            "description": "Custom pricing description"
        }
    ],
}

CUSTOM_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "The custom pricing",
            "priceType": "custom",
            "description": "Custom pricing description"
        },
        {
            "name": "plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1"
                }
            },
        }
    ],
}

BUNDLE_OFFERING = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
    "bundledProductOffering": [{"id": "6"}, {"id": "7"}],
}

OPEN_BUNDLE = deepcopy(BUNDLE_OFFERING)
OPEN_BUNDLE["productOfferingPrice"] = [{
    "id": "urn:product-offering-price:1234",
    "href": "urn:product-offering-price:1234"
}]

BUNDLE_MISSING_FIELD = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
}

BUNDLE_MISSING_ELEMS = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
    "bundledProductOffering": [{"id": "6"}],
}


MISSING_PRICETYPE = {
    "name": "plan",
    "price": {"currencyCode": "EUR"}
}

INVALID_PRICETYPE = {
    "name": "plan",
    "priceType": "invalid",
    "price": {"currencyCode": "EUR"}
}

MISSING_PERIOD = {
    "name": "plan",
    "priceType": "recurring",
    "price": {"currencyCode": "EUR"}
}

INVALID_PERIOD = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "invalid",
    "price": {"currencyCode": "EUR"},
}

MISSING_PRICE = {"name": "plan", "priceType": "recurring", "recurringChargePeriodType": "month"}

MISSING_CURRENCY = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "month",
    "price": {},
}

INVALID_CURRENCY = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "month",
    "price": {
        "unit": "invalid"
    }
}

MISSING_NAME = {"priceType": "recurring", "recurringChargePeriod": "monthly", "price": {}}

MULTIPLE_NAMES = {
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1.0"
                }
            },
        },
        {
            "name": "Plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1.0"
                }
            },
        },
    ],
}

OPEN_MIXED = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {"id": "urn:price:1234", "name": "open", "description": "Open offering"},
        {
            "name": "single",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1.0"
                }},
        },
    ],
}
