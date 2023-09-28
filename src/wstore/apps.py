from django.apps import AppConfig


def register_signals():
    from django.contrib.auth.models import User
    from django.db.models.signals import post_save
    from django.dispatch import receiver

    @receiver(post_save, sender=User, dispatch_uid="user_profile")
    def create_user_profile(sender, instance, created, **kwargs):
        from wstore.models import Organization, UserProfile

        if created:
            # Create a private organization for the user
            default_organization = Organization.objects.get_or_create(name=instance.username)
            default_organization[0].managers.append(instance.pk)
            default_organization[0].save()

            profile, created = UserProfile.objects.get_or_create(
                user=instance,
                current_roles=["customer"],
                current_organization=default_organization[0],
            )
            if instance.first_name and instance.last_name:
                profile.complete_name = instance.first_name + " " + instance.last_name
                profile.save()


class WstoreConfig(AppConfig):
    name = "wstore"
    verbose_name = "WStore"

    def ready(self):
        import sys

        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured

        from wstore.models import Context
        from wstore.ordering.inventory_client import InventoryClient
        from wstore.rss_adaptor.rss_manager import ProviderManager
        from wstore.store_commons.utils.url import is_valid_url

        # Creates a new user profile when an user is created
        # post_save.connect(create_user_profile, sender=User)
        register_signals()

        testing = sys.argv[1:2] == ["test"] or sys.argv[1:2] == ["migrate"]
        if not testing:
            # Validate that a correct site and local_site has been provided
            if not is_valid_url(settings.SITE) or not is_valid_url(settings.LOCAL_SITE):
                raise ImproperlyConfigured("SITE and LOCAL_SITE settings must be a valid URL")

            # Create context object if it does not exists
            if not len(Context.objects.all()):
                Context.objects.create(failed_cdrs=[], failed_upgrades=[])

            # inventory = InventoryClient()
            # inventory.create_inventory_subscription()

            # # Create RSS default aggregator and provider
            # credentials = {
            #     "user": settings.STORE_NAME,
            #     "roles": [settings.ADMIN_ROLE],
            #     "email": settings.WSTOREMAIL,
            # }
            # prov_manager = ProviderManager(credentials)

            # try:
            #     prov_manager.register_aggregator(
            #         {
            #             "aggregatorId": settings.WSTOREMAIL,
            #             "aggregatorName": settings.STORE_NAME,
            #             "defaultAggregator": True,
            #         }
            #     )
            # except Exception as e:  # If the error is a conflict means that the aggregator is already registered
            #     if e.response.status_code != 409:
            #         raise e
