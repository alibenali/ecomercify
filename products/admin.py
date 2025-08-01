from django.contrib import admin
from .models import Product, ProductVariant, VariantOption

class VariantOptionInline(admin.TabularInline):
    """Allows editing variant options (e.g., Color, Size) directly within ProductVariant."""
    model = VariantOption
    extra = 1  # Show 1 empty form for quick addition

class ProductVariantInline(admin.TabularInline):
    """Allows editing variants (e.g., different SKUs) within Product."""
    model = ProductVariant
    extra = 1  # Show 1 empty form for quick addition
    show_change_link = True  # Add link to edit variant separately
    inlines = [VariantOptionInline]  # Allow editing options inside the variant

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin panel for managing products."""
    list_display = ("name", "store", "SKU", "price", "stock_quantity", "created_at")
    search_fields = ("name", "SKU", "store__name")
    list_filter = ("store", "created_at")
    ordering = ("-created_at",)
    inlines = [ProductVariantInline]  # Manage variants directly within products
    readonly_fields = ("created_at",)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Admin panel for managing product variants."""
    list_display = ("product", "SKU", "price", "stock_quantity", "created_at")
    search_fields = ("product__name", "SKU")
    list_filter = ("product", "created_at")
    ordering = ("-created_at",)
    inlines = [VariantOptionInline]  # Manage variant options directly inside the variant
    readonly_fields = ("created_at",)

@admin.register(VariantOption)
class VariantOptionAdmin(admin.ModelAdmin):
    """Admin panel for managing variant options."""
    list_display = ("variant", "name", "value", "created_at")
    search_fields = ("variant__SKU", "name", "value")
    list_filter = ("name", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
