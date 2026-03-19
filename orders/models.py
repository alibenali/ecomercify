from django.db import models
from django.conf import settings
from django.db.models import F, Sum
from products.models import Product, ProductOptionValue, ProductVariant
from stores.models import Store
from landingpages.models import LandingPage


class Order(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("in_confirmation", "In Confirmation"),
        ("in_delivery", "In Delivery"),
        ("delivered", "Delivered"),
        ("canceled", "Canceled"),
        ("archived", "Archived"),
        ("blocked", "Blocked"),
    ]

    DELIVERY_METHOD_CHOICES = [
        ("home_delivery", "Delivery to home"),
        ("stop_desk", "Stop desk"),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_method = models.CharField(
        max_length=255,
        choices=DELIVERY_METHOD_CHOICES,
        default="home_delivery",
    )
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    http_referer = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="in_progress",
    )
    landing_page = models.ForeignKey(
        LandingPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def sub_total(self):
        result = self.items.aggregate(
            sub_total=Sum(F("price_per_unit") * F("quantity"))
        ).get("sub_total")
        return result if result is not None else 0

    @property
    def total_price(self):
        return float(self.sub_total) + float(self.delivery_cost) - float(self.discount)

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    variant_values = models.ManyToManyField(
        ProductOptionValue,
        blank=True,
        related_name="order_items",
    )
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def get_sku(self):
        if self.variant:
            return self.variant.SKU
        elif self.variant_values.exists():
            return ", ".join(
                [v.option.name + ":" + v.value for v in self.variant_values.all()]
            )
        return self.product.SKU if self.product else None

    def get_name(self):
        name = self.product.name if self.product else ""
        if self.variant:
            variant_values_str = ", ".join(
                [f"{v.option.name}: {v.value}" for v in self.variant.option_values.all()]
            )
            return f"{name} ({variant_values_str})"
        elif self.variant_values.exists():
            variants = ", ".join(
                [f"{v.option.name}: {v.value}" for v in self.variant_values.all()]
            )
            return f"{name} ({variants})"
        return name

    def get_image(self):
        if self.variant and self.variant.image:
            return self.variant.image.url
        if self.variant_values.exists():
            for v in self.variant_values.all():
                if v.image:
                    return v.image.url
        if self.product and self.product.image:
            return self.product.image.url
        return None

    def clean(self):
        if not self.product:
            raise ValidationError("An order item must have a product.")
        if self.variant and not self.product.variants.filter(pk=self.variant.pk).exists():
            raise ValidationError("Selected variant does not belong to the product.")
        if self.variant and self.variant_values.exists():
            raise ValidationError("Only one of variant or variant_values should be selected.")


class StatusHistory(models.Model):
    """
    Generic history of any change made to an order or its items.
    Keeps backward‑compatible status fields, but can also track
    price/quantity, delivery cost, discounts, and item add/delete.
    """

    class Action(models.TextChoices):
        STATUS_CHANGE = "status_change", "Status change"
        ORDER_UPDATE = "order_update", "Order updated"
        ITEM_UPDATE = "item_update", "Item updated"
        ITEM_ADD = "item_add", "Item added"
        ITEM_DELETE = "item_delete", "Item deleted"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    order_item = models.ForeignKey(
        "orders.OrderItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="history",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )

    # Optional status info (for status_change)
    previous_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        null=True,
        blank=True,
    )
    new_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        null=True,
        blank=True,
    )

    # Generic field/value tracking
    field_name = models.CharField(max_length=50, null=True, blank=True)
    previous_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)

    note = models.TextField(blank=True, null=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        base = f"Order #{self.order.id}"
        if self.action == self.Action.STATUS_CHANGE:
            return f"{base} - {self.previous_status} → {self.new_status} by {self.changed_by}"
        if self.field_name:
            return f"{base} - {self.field_name}: {self.previous_value} → {self.new_value} by {self.changed_by}"
        return f"{base} - {self.action} by {self.changed_by}"
