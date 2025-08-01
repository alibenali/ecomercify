from django.db import models
from stores.models import Store
from django.conf import settings

class Product(models.Model):
    """Base product without specific variations"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    SKU = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="product_base/", default="products/default.png", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_image(self):
        return self.image.url if self.image else settings.MEDIA_URL + "products/default.png"
    def __str__(self):
        return f"{self.name} - {self.store.name}"

class ProductVariant(models.Model):
    """Each variant has its own SKU, price, stock, and image"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    SKU = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="product_variants/", default="products/default.png", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.product.name} - {self.SKU}"

class VariantOption(models.Model):
    """Stores attributes like 'Color: Red' or 'Size: L' for each variant"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=255)  # e.g., "Color", "Size"
    value = models.CharField(max_length=255)  # e.g., "Red", "Large"
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.variant} - {self.name}: {self.value}"
