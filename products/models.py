from django.db import models
from stores.models import Store
from django.conf import settings

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    SKU = models.CharField(max_length=255, unique=True)
    fake_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="product_base/", default="products/default.png", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_image(self):
        return self.image.url

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class ProductOption(models.Model):
    """E.g., Size, Color"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=255)  # e.g., "Size"

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionValue(models.Model):
    """E.g., Large, Red"""
    option = models.ForeignKey(ProductOption, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=255)  # e.g., "Large"

    def __str__(self):
        return f"{self.option.name}: {self.value}"


class ProductVariant(models.Model):
    """A specific combination of option values"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    SKU = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="product_variants/", blank=True, null=True)
    option_values = models.ManyToManyField(ProductOptionValue, related_name="variants")

    def __str__(self):
        values = ", ".join([v.value for v in self.option_values.all()])
        return f"{self.product.name} - {values}"
