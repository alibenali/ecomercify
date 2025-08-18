from django.db.models.signals import post_save
from django.dispatch import receiver
from dashboard.models import City
from .models import Store  # since you already import Store inside City, but safe to import here


@receiver(post_save, sender=Store)
def create_cities_for_store(sender, instance, created, **kwargs):
    """Auto create all cities when a new store is created"""
    if created:
        for city_name, _ in City.CITY_CHOICES:
            City.objects.get_or_create(
                store=instance,
                name=city_name,
                defaults={"delivery_cost": 0}
            )


def backfill_cities():
    """Ensure all existing stores have all cities"""
    for store in Store.objects.all():
        for city_name, _ in City.CITY_CHOICES:
            City.objects.get_or_create(
                store=store,
                name=city_name,
                defaults={"delivery_cost": 0}
            )
            pass
