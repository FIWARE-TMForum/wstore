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


BILLING_ACCOUNT_HREF = "http://serverlocation:port/billingManagement/billingAccount/1789"

OFFERING = {
    "id": "5",
    "name": "Example offering",
    "version": "1.0",
    "description": "Example offering description",
    "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)",
    "productSpecification": {
        "href": "http://producturl.com/"
    },
    "serviceCandidate": {
        "id": "productClass"
    }
}

PRODUCT = {
    "id": "5",
    "relatedParty": [{
        "id": "test_user",
        "role": "Owner"
    }, {
        "id": "test_user2",
        "role": "Partner"
    }]
}

BILLING_ACCOUNT = {
    "customerAccount": {
        "href": "http://serverlocation:port/customerManagement/customerAccount/1789"
    }
}


CUSTOMER_ACCOUNT = {
    "customer": {
        "href": "http://serverlocation:port/customerManagement/customer/19"
    }
}

CUSTOMER = {
    "contactMedium": [{
        "type": "PostalAddress",
        "medium": {
            "streetOne": "Campus de Montegancedo",
            "streetTwo": "s/n",
            "postcode": "28660",
            "city": "Madrid",
            "stateOrProvince": "Madrid",
            "country": "Spain"
        }
    }]
}

BASIC_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "description": "",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
         "billingAccount": [{
               "id": "1789",
               "href": BILLING_ACCOUNT_HREF
         }],
         "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
         "product": {
             "productPrice": [{
             "priceType": "one time",
             "unitOfMeasure": "",
             "price": {
                "amount": "12.00",
                "currency": "EUR",
             },
             "recurringChargePeriod": "",
             "name": "One Time",
             "validFor": {
                 "startDateTime": "2013-04-19T20:42:23.000+0000",
                 "endDateTime": "2013-06-19T04:00:00.000+0000"
             }
            }]
         }
      }
   ]
}


BASIC_PRICING = {
    "priceType": "one time",
    "unitOfMeasure": "",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "One Time",
}

RECURRING_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
         "billingAccount": [{
               "id": "1789",
               "href": BILLING_ACCOUNT_HREF
         }],
         "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
         "product": {
             "productPrice": [{
             "priceType": "recurring",
             "unitOfMeasure": "",
             "price": {
                "amount": "12.00",
                "currency": "EUR",
             },
             "recurringChargePeriod": "monthly",
             "name": "Recurring Monthly Charge",
             "description": "A monthly recurring payment",
             "validFor": {
                 "startDateTime": "2013-04-19T20:42:23.000+0000",
                 "endDateTime": "2013-06-19T04:00:00.000+0000"
             }
            }]
         }
      }
   ]
}

RECURRING_PRICING = {
    "priceType": "recurring",
    "unitOfMeasure": "",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "monthly",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
}

USAGE_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
         "billingAccount": [{
               "id": "1789",
               "href": BILLING_ACCOUNT_HREF
         }],
         "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
         "product": {
             "productPrice": [{
             "priceType": "Usage",
             "unitOfMeasure": "megabyte",
             "price": {
                "amount": "12.00",
                "currency": "EUR",
             },
             "recurringChargePeriod": "",
             "name": "Recurring Monthly Charge",
             "description": "A monthly recurring payment",
             "validFor": {
                 "startDateTime": "2013-04-19T20:42:23.000+0000",
                 "endDateTime": "2013-06-19T04:00:00.000+0000"
             }
            }]
         }
      }
   ]
}

USAGE_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    }
}

FREE_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
         "billingAccount": [{
               "id": "1789",
               "href": BILLING_ACCOUNT_HREF
         }],
         "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
         "product": {
         }
      }
   ]
}

NOPRODUCT_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
         "billingAccount": [{
               "id": "1789",
               "href": BILLING_ACCOUNT_HREF
         }],
         "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
      }
   ]
}

DISCOUNT_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Shipping Discount",
        "description": "One time shipping discount",
        "validFor": {
            "startDateTime": "2013-04-19T16:42:23.0Z"
        },
        "priceType": "one time",
        "unitOfMeasure": "",
        "price": {
            "percentage": 50
        },
        "recurringChargePeriod": "",
        "priceCondition": ""
    }
}

RECURRING_FEE_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Recurring Fee",
        "description": "A fixed fee added in every charge",
        "validFor": {
            "startDateTime": "2013-04-19T16:42:23.0Z"
        },
        "priceType": "recurring",
        "unitOfMeasure": "",
        "price": {
            "taxIncludedAmount": "1.00",
            "dutyFreeAmount": "0.80",
            "taxRate": "20.00",
            "currencyCode": "EUR",
            "percentage": 0
        },
        "recurringChargePeriod": "",
        "priceCondition": "gt 300.00"
    }
}

DOUBLE_PRICE_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Initial fee",
        "description": "An initial fee for the charge",
        "validFor": {
            "startDateTime": "2013-04-19T16:42:23.0Z"
        },
        "priceType": "one time",
        "unitOfMeasure": "",
        "price": {
            "taxIncludedAmount": "8.00",
            "dutyFreeAmount": "6.00",
            "taxRate": "20.00",
            "currencyCode": "EUR",
            "percentage": 0
        },
        "recurringChargePeriod": ""
    }
}

DOUBLE_USAGE_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Initial fee",
        "description": "An initial fee for the charge",
        "validFor": {
            "startDateTime": "2013-04-19T16:42:23.0Z"
        },
        "priceType": "usage",
        "unitOfMeasure": "second",
        "price": {
            "taxIncludedAmount": "8.00",
            "dutyFreeAmount": "6.00",
            "taxRate": "20.00",
            "currencyCode": "EUR",
            "percentage": 0
        },
        "recurringChargePeriod": ""
    }
}

USAGE_ALTERATION_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Initial fee",
        "priceType": "usage",
        "unitOfMeasure": "",
        "price": {
            "taxIncludedAmount": "8.00",
            "dutyFreeAmount": "6.00",
            "taxRate": "20.00",
            "currencyCode": "EUR",
            "percentage": 0
        },
        "recurringChargePeriod": "",
        "priceCondition": "gt 300"
    }
}

INV_CONDITION_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
    "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "Initial fee",
        "priceType": "recurring",
        "unitOfMeasure": "",
        "price": {
            "percentage": 20
        },
        "recurringChargePeriod": "",
        "priceCondition": "gty 300"
    }
}

INV_ALTERATION_PRICING = {
    "priceType": "Usage",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    },
    "productOfferPriceAlteration": {
        "name": "an alteration"
    }
}

INVALID_STATE_ORDER = {
    "id": "12",
    "state": "inProgress"
}

INVALID_MODEL_ORDER = {
    "id": "12",
    "state": "Acknowledged",
    "orderItem": [
      {
         "id": "1",
         "action": "add",
          "productOffering": {
            "id": "20",
            "href": "http://localhost:8004/DSProductCatalog/api/catalogManagement/v2/productOffering/20:(2.0)"
         },
         "product": {
             "productPrice": [{
                "priceType": "Invalid",
                "unitOfMeasure": "megabyte",
                "price": {
                    "amount": "12.00",
                    "currency": "EUR",
                },
                "recurringChargePeriod": "",
                "name": "Recurring Monthly Charge",
                "description": "A monthly recurring payment",
                "validFor": {
                    "startDateTime": "2013-04-19T20:42:23.000+0000",
                    "endDateTime": "2013-06-19T04:00:00.000+0000"
                }
            }]
         }
      }
   ]
}

INVALID_MODEL_PRICING = {
    "priceType": "Invalid",
    "unitOfMeasure": "megabyte",
    "price": {
        "taxIncludedAmount": "12.00",
        "dutyFreeAmount": "10.00",
        "taxRate": "20.00",
        "currencyCode": "EUR",
        "percentage": 0
    },
    "recurringChargePeriod": "",
    "name": "Recurring Monthly Charge",
    "description": "A monthly recurring payment",
    "validFor": {
        "startDateTime": "2013-04-19T20:42:23.000+0000",
        "endDateTime": "2013-06-19T04:00:00.000+0000"
    }
}