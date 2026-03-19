from django.db import models
from stores.models import Store, FacebookPixel
from django.conf import settings


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    SKU = models.CharField(max_length=255, unique=True)
    fake_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    custom_pixels = models.ManyToManyField(FacebookPixel, blank=True, related_name="products")

    image = models.ImageField(upload_to="product_base/", default="products/default.png", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_image(self):
        if self.image:
            return self.image.url
        return "/media/products/default.png"

    def get_pixels(self):
        """Return product pixels if set, otherwise store pixels."""
        if self.custom_pixels.exists():
            return self.custom_pixels.all()
        return self.store.pixels.all()

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class ProductOption(models.Model):
    """E.g., Size, Color"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionValue(models.Model):
    """E.g., Large, Red"""
    option = models.ForeignKey(ProductOption, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.option.name}: {self.value}"



class ProductVariant(models.Model):

    class VariantType(models.TextChoices):
        OPTION = "option", "Option"   # e.g. Color / Size combination
        OFFER  = "offer",  "Offer"    # e.g. Buy 2 for $15

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    variant_type = models.CharField(
        max_length=10,
        choices=VariantType.choices,
        default=VariantType.OPTION,
    )
    SKU = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="product_variants/", blank=True, null=True)

    # ── Option-variant fields ────────────────────────────────────────────────
    option_values = models.ManyToManyField(
        ProductOptionValue,
        related_name="variants",
        blank=True,
    )

    # ── Offer-variant fields ─────────────────────────────────────────────────
    offer_label = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text='Display label shown to the customer, e.g. "Buy 2 for $15" (offers only).',
    )

    def is_offer(self):
        return self.variant_type == self.VariantType.OFFER

    def is_option(self):
        return self.variant_type == self.VariantType.OPTION

    def __str__(self):
        if self.is_offer():
            return f"{self.product.name} – {self.offer_label or 'Offer'}"
        values = ", ".join([v.value for v in self.option_values.all()])
        return f"{self.product.name} – {values}"