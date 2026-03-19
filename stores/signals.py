# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Store, City
from .choices import CITY_CHOICES_BY_COUNTRY

@receiver(post_save, sender=Store)
def create_default_cities(sender, instance, created, **kwargs):
    """
    Auto-create cities for a new store based on owner's country.
    """
    if created:  # Only run when store is first created
        # Get owner's country
        owner_country = getattr(instance.owner, 'country', None)
        
        if not owner_country:
            return  # Or set a default country
            
        # Get cities for this country
        cities_data = CITY_CHOICES_BY_COUNTRY.get(owner_country, [])
        
        # Bulk create cities for better performance
        cities_to_create = [
            City(
                store=instance,
                name=city_name,
                delivery_cost=0.00  # Default cost, owner can update later
            )
            for city_code, city_name in cities_data
        ]
        
        if cities_to_create:
            City.objects.bulk_create(cities_to_create, ignore_conflicts=True)