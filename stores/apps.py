from django.apps import AppConfig

class StoresConfig(AppConfig):  # change name if your app is not "stores"
    default_auto_field = "django.db.models.BigAutoField"
    name = "stores"

    # def ready(self):
    #     from . import signals
    #     signals.backfill_cities()
