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



from wstore.models import UserProfile


def rollback(purchase):
    # If the purchase state is paid means that the purchase has been made
    # so the models must not be deleted
    offering = purchase.offering

    if purchase.state != 'paid':

        # Check that the payment has been made
        contract = True
        try:
            contr = purchase.contract
        except:
            contract = False

        to_del = True
        if contract:
            # If the charges field contains any charge means that it is not
            # the first charge so the models cannot be deleted
            if len(contr.charges) > 0:
                purchase.state = 'paid'
                purchase.save()
                to_del = False

        if to_del:
            # Check organization owned
            if purchase.organization_owned:
                org = purchase.owner_organization
                if purchase.offering.pk in org.offerings_purchased:
                    org.offerings_purchased.remove(purchase.offering.pk)
                    org.save()

            # Delete the offering from the user profile
            user_profile = UserProfile.objects.get(user=purchase.customer)
            if purchase.offering.pk in user_profile.offerings_purchased:
                user_profile.offerings_purchased.remove(purchase.offering.pk)
                user_profile.save()

            # Delete the contract
            if contract:
                purchase.contract.delete()
            # Delete the Purchase
            purchase.delete()

    # If the purchase is paid the offering must be included in the customer
    # asset_manager purchased list
    else:
        if purchase.organization_owned:
            org = purchase.owner_organization
            if not purchase.offering.pk in org.offerings_purchased:
                org.offerings_purchased.append(purchase.offering.pk)
                org.save()
        else:
            profile = purchase.customer.userprofile
            if not purchase.offering.pk in profile.offerings_purchased:
                profile.offerings_purchased.append(purchase.offering.pk)
                profile.save()


# This class is used as a decorator to avoid inconsistent states in
# purchases models in case of Exception
class PurchaseRollback():
    _funct = None

    def __init__(self, funct):
        self._funct = funct

    def __call__(self, user, offering, org_owned=False, payment_info={}):
        try:
            # Call the decorated function
            result = self._funct(user, offering, org_owned, payment_info)
        except Exception as e:
            if str(e) != "This offering can't be purchased" and str(e) != 'The offering has been already purchased'\
                    and str(e) != 'Invalid payment method' and str(e) != 'Invalid credit card info'\
                    and str(e) != 'The customer does not have a tax address' and str(e) != 'The customer does not have payment info'\
                    and str(e) != 'Missing a required field in the tax address. It must contain street, postal, city, province and country'\
                    and str(e) != 'Open asset_manager cannot be purchased' \
                    and str(e) != 'You must accept the terms and conditions of the offering to acquire it':

                # Get the purchase
                if org_owned:
                    user_profile = UserProfile.objects.get(user=user)
                    purchase = Purchase.objects.get(owner_organization=user_profile.current_organization, offering=offering)
                else:
                    purchase = Purchase.objects.get(customer=user, offering=offering, organization_owned=False)
                rollback(purchase)

            raise e
        return result
