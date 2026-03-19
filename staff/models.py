from django.db import models
from django.conf import settings
from stores.models import Store

from staff.choices import ROLE_CHOICES, get_default_permissions_for_role


class Staff(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_memberships",
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    # Explicit permissions override role defaults. Null/empty = use role defaults.
    # List of codenames e.g. ["view_orders", "edit_orders"]
    permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} at {self.store.name}"

    def get_effective_permissions(self):
        """Return list of permission codenames (from explicit or role defaults)."""
        if self.permissions:
            return self.permissions
        return get_default_permissions_for_role(self.role)


