from django.views.generic import ListView
from .models import Product, ProductVariant, ProductOption, ProductOptionValue
from stores.models import Store  # Assuming user selects or owns store
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction

# Create your views here.
class ProductListView(ListView):
    model = Product
    template_name = "dashboard/products/products_list.html"
    context_object_name = "products"
    paginate_by = 10  # Adjust pagination as needed
    
    def get_queryset(self):
        return Product.objects.all().order_by("-created_at")
    


def public_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "dashboard/products/product_detail.html", {"product": product})

def add_product(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Get base product data
                store = Store.objects.first()  # TODO: replace with store from logged-in user
                name = request.POST.get("name")
                sku = request.POST.get("SKU")
                price = request.POST.get("price")
                fake_price = request.POST.get("fake_price")
                description = request.POST.get("description")
                image = request.FILES.get("image")

                # Create product
                product = Product.objects.create(
                    store=store,
                    name=name,
                    SKU=sku,
                    price=price,
                    fake_price=fake_price,
                    description=description,
                    image=image
                )

                # Check if variants were added
                variants_data = {}
                for key, value in request.POST.items():
                    if key.startswith("variants["):
                        # Extract index and field name
                        parts = key.split("[")
                        index = parts[1].replace("]", "")
                        field = parts[2].replace("]", "").strip()
                        
                        if index not in variants_data:
                            variants_data[index] = {"options": []}

                        if field == "SKU":
                            variants_data[index]["SKU"] = value
                        elif field == "price":
                            variants_data[index]["price"] = value
                        elif field == "stock_quantity":
                            variants_data[index]["stock_quantity"] = value
                        elif field == "options":
                            # This won't trigger here because options have deeper nesting
                            pass

                # Get variant images
                for key, file in request.FILES.items():
                    if key.startswith("variants[") and "image" in key:
                        parts = key.split("[")
                        index = parts[1].replace("]", "")
                        if index in variants_data:
                            variants_data[index]["image"] = file

                # Process options separately
                for key, value in request.POST.items():
                    if "options" in key and ("name" in key or "value" in key):
                        parts = key.split("[")
                        index = parts[1].replace("]", "")
                        if index in variants_data:
                            # Ensure there is an options list
                            if "options" not in variants_data[index]:
                                variants_data[index]["options"] = []

                            if "name" in key:
                                variants_data[index]["options"].append({"name": value, "value": None})
                            elif "value" in key:
                                # Attach to the last added name
                                if variants_data[index]["options"]:
                                    variants_data[index]["options"][-1]["value"] = value

                # Create variants and their options
                for var_index, vdata in variants_data.items():
                    variant = ProductVariant.objects.create(
                        product=product,
                        SKU=vdata.get("SKU", ""),
                        price=vdata.get("price", 0),
                        stock_quantity=vdata.get("stock_quantity", 0),
                        image=vdata.get("image", None)
                    )

                    for opt in vdata.get("options", []):
                        if not opt.get("name") or not opt.get("value"):
                            continue
                        # Create option if not exists
                        option_obj, _ = ProductOption.objects.get_or_create(
                            product=product,
                            name=opt["name"]
                        )
                        # Create option value
                        value_obj, _ = ProductOptionValue.objects.get_or_create(
                            option=option_obj,
                            value=opt["value"]
                        )
                        variant.option_values.add(value_obj)

                messages.success(request, "Product and variants added successfully!")
                return redirect("products:products_list")  # Change to your actual URL name

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, "dashboard/products/add_product.html")


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        # --- Update base product fields ---
        product.name = request.POST.get("name", "").strip()
        product.SKU = request.POST.get("SKU", "").strip()
        product.price = request.POST.get("price") or 0
        product.fake_price = request.POST.get("fake_price") or 0
        product.description = request.POST.get("description", "").strip()
        if request.FILES.get("image"):
            product.image = request.FILES["image"]
        product.save()

        # =====================
        # EXISTING VARIANTS
        # =====================
        variant_ids = request.POST.getlist("variant_ids[]")
        variant_SKUs = request.POST.getlist("variant_SKUs[]")
        variant_prices = request.POST.getlist("variant_prices[]")
        variant_stocks = request.POST.getlist("variant_stocks[]")
        variant_deletes = request.POST.getlist("variant_delete[]")
        variant_images = request.FILES.getlist("variant_images[]")

        for idx, vid in enumerate(variant_ids):
            variant = get_object_or_404(ProductVariant, pk=vid, product=product)

            if variant_deletes[idx] == "true":
                variant.delete()
                continue

            variant.SKU = variant_SKUs[idx]
            variant.price = variant_prices[idx] or 0
            variant.stock_quantity = variant_stocks[idx] or 0
            if idx < len(variant_images) and variant_images[idx]:
                variant.image = variant_images[idx]
            variant.save()

            # Remove old option links (not deleting the actual option values)
            variant.option_values.clear()

            # Option names/values for this variant
            option_names = request.POST.getlist(f"option_names_{vid}[]")
            option_values = request.POST.getlist(f"option_values_{vid}[]")

            for name, value in zip(option_names, option_values):
                name = (name or "").strip()
                value = (value or "").strip()
                if not name or not value:
                    continue

                option_obj, _ = ProductOption.objects.get_or_create(
                    product=product, name=name
                )
                value_obj, _ = ProductOptionValue.objects.get_or_create(
                    option=option_obj, value=value
                )
                variant.option_values.add(value_obj)

        # =====================
        # NEW VARIANTS
        # =====================
        if "new_variants" in request.POST:
            for index, new_variant in request.POST.lists():
                if not index.startswith("new_variants["):
                    continue

            new_variants = request.POST.getlist("new_variants")
            # Since the template sends them as dict-like keys,
            # we'll loop until no more keys found
            idx = 0
            while True:
                sku_key = f"new_variants[{idx}][SKU]"
                if sku_key not in request.POST:
                    break

                sku = request.POST.get(sku_key, "").strip()
                price = request.POST.get(f"new_variants[{idx}][price]") or 0
                stock = request.POST.get(f"new_variants[{idx}][stock_quantity]") or 0
                image = request.FILES.get(f"new_variants[{idx}][image]")

                if not sku and not price:
                    idx += 1
                    continue

                variant = ProductVariant.objects.create(
                    product=product,
                    SKU=sku,
                    price=price,
                    stock_quantity=stock,
                    image=image if image else None,
                )

                opt_names = request.POST.getlist(f"new_variants[{idx}][options][][name]")
                opt_values = request.POST.getlist(f"new_variants[{idx}][options][][value]")

                for name, value in zip(opt_names, opt_values):
                    name = (name or "").strip()
                    value = (value or "").strip()
                    if not name or not value:
                        continue

                    option_obj, _ = ProductOption.objects.get_or_create(
                        product=product, name=name
                    )
                    value_obj, _ = ProductOptionValue.objects.get_or_create(
                        option=option_obj, value=value
                    )
                    variant.option_values.add(value_obj)

                idx += 1

        return redirect("products:products_list")  # adjust to your route name

    return render(request, "dashboard/products/product_edit.html", {"product": product})