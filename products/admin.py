from django.contrib import admin
from .models import Product, ProductOption, ProductOptionValue, ProductVariant


class ProductOptionValueInline(admin.TabularInline):
    model = ProductOptionValue
    extra = 1


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    filter_horizontal = ("option_values",)  # Easier multi-select for values


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "SKU", "price", "store")
    search_fields = ("name", "SKU")
    list_filter = ("store",)
    inlines = [ProductOptionInline, ProductVariantInline]


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "product")
    search_fields = ("name", "product__name")
    inlines = [ProductOptionValueInline]


@admin.register(ProductOptionValue)
class ProductOptionValueAdmin(admin.ModelAdmin):
    list_display = ("value", "option")
    search_fields = ("value", "option__name", "option__product__name")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "get_option_values", "SKU", "price", "stock_quantity")
    search_fields = ("SKU", "product__name")
    filter_horizontal = ("option_values",)

    def get_option_values(self, obj):
        return ", ".join([v.value for v in obj.option_values.all()])
    get_option_values.short_description = "Options"
