from django.db import models
from django.conf import settings
from django.db.models import Sum
from products.models import Product, ProductVariant
from stores.models import Store

class Order(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('in_confirmation', 'In Confirmation'),
        ('in_delivery', 'In Delivery'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('home_delivery', 'Delivery to home'),
        ('stop_desk', 'Stop desk'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_method = models.CharField(max_length=255, choices=DELIVERY_METHOD_CHOICES, default='home_delivery')
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    http_referer = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def sub_total(self):
        return self.items.aggregate(sub_total=Sum("price_per_unit") * Sum("quantity"))["sub_total"] or 0
    
    @property
    def total_price(self):
        return float(self.sub_total) + float(self.delivery_cost) - float(self.discount)
    
    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    variation = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def get_product(self):
        return self.variation if self.variation else self.product

    def get_image(self):
        if not self.get_product().image:
            return None
        return self.get_product().image.url

    def get_sku(self):
        return self.get_product().SKU

    def get_name(self):
        return self.variation.product.name if self.variation else self.product.name



    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.product and not self.variation:
            raise ValidationError("You must provide either a product or a variation.")
        if self.product and self.variation:
            raise ValidationError("Only one of product or variation should be selected.")

class StatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order.id} - {self.previous_status} → {self.new_status} by {self.changed_by}"
