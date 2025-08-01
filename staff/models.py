from django.db import models
from django.conf import settings
from stores.models import Store

class Staff(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="staff")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff")
    role = models.CharField(max_length=50, choices=[
        ('manager', 'Manager'),
        ('confirmation_assistant', 'Confirmation Assistant'),
        ('delivery_assistant', 'Delivery Assistant'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} at {self.store.name}"


