from django.views.generic import ListView
from .models import Product, ProductVariant, ProductOption, ProductOptionValue
from stores.models import Store
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from landingpages.models import LandingPage
from staff.utils import user_can_access_store, user_can_manage_store

# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------

def get_accessible_stores(user):
    """All stores the user owns or is staff at."""
    owned = Store.objects.filter(owner=user)
    staffed = Store.objects.filter(staff__user=user)
    return (owned | staffed).distinct()


def get_product_or_403(pk, user, write=False):
    """
    Fetch a product and check access.
    - write=False: owner or any staff can access (read)
    - write=True:  owner or manager staff only (create/edit/delete)
    """
    product = get_object_or_404(Product, pk=pk)
    check = user_can_manage_store if write else user_can_access_store
    if not check(user, product.store):
        raise PermissionDenied
    return product


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "dashboard/products/products_list.html"
    context_object_name = "products"
    paginate_by = 999

    def get_queryset(self):
        return Product.objects.filter(
            store__in=get_accessible_stores(self.request.user)
        ).order_by("-created_at")


def public_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})


@login_required
def product_detail(request, pk):
    product = get_product_or_403(pk, request.user, write=False)
    return render(request, "dashboard/products/product_detail.html", {"product": product})

@login_required
def add_product(request):
    from django.db.models import Q
    manageable_stores = (
        Store.objects.filter(owner=request.user) |
        Store.objects.filter(
            staff__user=request.user
        ).filter(
            Q(staff__role="manager") | Q(staff__permissions__contains=["manage_products"])
        )
    ).distinct().order_by("name")

    if request.method == "POST":
        try:
            with transaction.atomic():
                store_id = request.POST.get("store_id") or request.POST.get("store")
                store = get_object_or_404(Store, pk=store_id)

                if not user_can_manage_store(request.user, store):
                    raise PermissionDenied

                product = Product.objects.create(
                    store=store,
                    name=request.POST.get("name"),
                    SKU=request.POST.get("SKU"),
                    price=request.POST.get("price"),
                    fake_price=request.POST.get("fake_price"),
                    description=request.POST.get("description"),
                    image=request.FILES.get("image"),
                )

                # ── Landing page ──────────────────────────────────────────
                landing_page = LandingPage.objects.create(
                    product=product,
                    code=request.POST.get("SKU"),
                )
                # ── Parse variants ──────────────────────────────────────────
                variants_data = {}
                for key, value in request.POST.items():
                    if not key.startswith("variants["):
                        continue
                    parts = key.split("[")
                    idx   = parts[1].rstrip("]")
                    field = parts[2].rstrip("]").strip()

                    if idx not in variants_data:
                        variants_data[idx] = {"options": [], "type": "option"}

                    if field in ("SKU", "price", "stock_quantity", "type", "offer_label"):
                        variants_data[idx][field] = value

                # Variant images
                for key, file in request.FILES.items():
                    if key.startswith("variants[") and "image" in key:
                        idx = key.split("[")[1].rstrip("]")
                        if idx in variants_data:
                            variants_data[idx]["image"] = file

                # Option name/value pairs
                for key, value in request.POST.items():
                    if "options" not in key:
                        continue
                    parts = key.split("[")
                    idx = parts[1].rstrip("]")
                    if idx not in variants_data:
                        continue
                    field = parts[4].rstrip("]") if len(parts) > 4 else ""
                    if field == "name":
                        variants_data[idx]["options"].append({"name": value, "value": None})
                    elif field == "value" and variants_data[idx]["options"]:
                        variants_data[idx]["options"][-1]["value"] = value

                # ── Create variants ─────────────────────────────────────────
                for vdata in variants_data.values():
                    variant_type = vdata.get("type", "option")

                    variant = ProductVariant.objects.create(
                        product=product,
                        variant_type=variant_type,
                        SKU=vdata.get("SKU", ""),
                        price=vdata.get("price") or 0,
                        stock_quantity=vdata.get("stock_quantity") or 0,
                        image=vdata.get("image") or None,
                        offer_label=vdata.get("offer_label", "") if variant_type == "offer" else "",
                    )

                    # Only process option values for option-type variants
                    if variant_type == "option":
                        for opt in vdata.get("options", []):
                            if not opt.get("name") or not opt.get("value"):
                                continue
                            option_obj, _ = ProductOption.objects.get_or_create(
                                product=product, name=opt["name"]
                            )
                            value_obj, _ = ProductOptionValue.objects.get_or_create(
                                option=option_obj, value=opt["value"]
                            )
                            variant.option_values.add(value_obj)

                messages.success(request, "Product added successfully!")
                return redirect("products:products_list")

        except PermissionDenied:
            raise
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    selected_store_id = request.POST.get("store_id") or request.POST.get("store") or ""
    return render(
        request,
        "dashboard/products/add_product.html",
        {"stores": manageable_stores, "selected_store_id": selected_store_id},
    )

@login_required
def product_edit(request, pk):
    product = get_product_or_403(pk, request.user, write=True)

    if request.method == "POST":
        product.name        = request.POST.get("name", "").strip()
        product.SKU         = request.POST.get("SKU", "").strip()
        product.price       = request.POST.get("price") or 0
        product.fake_price  = request.POST.get("fake_price") or 0
        product.description = request.POST.get("description", "").strip()
        if request.FILES.get("image"):
            product.image = request.FILES["image"]
        product.save()

        # ── Update existing variants ────────────────────────────────────────
        variant_ids         = request.POST.getlist("variant_ids[]")
        variant_SKUs        = request.POST.getlist("variant_SKUs[]")
        variant_prices      = request.POST.getlist("variant_prices[]")
        variant_stocks      = request.POST.getlist("variant_stocks[]")
        variant_deletes     = request.POST.getlist("variant_delete[]")
        variant_types       = request.POST.getlist("variant_types[]")
        variant_offer_labels = request.POST.getlist("variant_offer_labels[]")
        variant_images      = request.FILES.getlist("variant_images[]")

        for idx, vid in enumerate(variant_ids):
            variant = get_object_or_404(ProductVariant, pk=vid, product=product)

            if variant_deletes[idx] == "true":
                variant.delete()
                continue

            variant_type = variant_types[idx] if idx < len(variant_types) else variant.variant_type

            variant.SKU            = variant_SKUs[idx]
            variant.price          = variant_prices[idx] or 0
            variant.stock_quantity = variant_stocks[idx] or 0
            variant.variant_type   = variant_type
            variant.offer_label    = variant_offer_labels[idx] if variant_type == "offer" and idx < len(variant_offer_labels) else ""

            if idx < len(variant_images) and variant_images[idx]:
                variant.image = variant_images[idx]
            variant.save()

            # Only update option values for option-type variants
            if variant_type == "option":
                variant.option_values.clear()
                opt_names  = request.POST.getlist(f"option_names_{vid}[]")
                opt_values = request.POST.getlist(f"option_values_{vid}[]")
                for name, value in zip(opt_names, opt_values):
                    name, value = name.strip(), value.strip()
                    if not name or not value:
                        continue
                    option_obj, _ = ProductOption.objects.get_or_create(product=product, name=name)
                    value_obj, _  = ProductOptionValue.objects.get_or_create(option=option_obj, value=value)
                    variant.option_values.add(value_obj)
            else:
                # Offer variant — clear any leftover option values
                variant.option_values.clear()

        # ── Create new variants ─────────────────────────────────────────────
        idx = 0
        while True:
            sku_key = f"new_variants[{idx}][SKU]"
            if sku_key not in request.POST:
                break

            sku          = request.POST.get(sku_key, "").strip()
            price        = request.POST.get(f"new_variants[{idx}][price]") or 0
            stock        = request.POST.get(f"new_variants[{idx}][stock_quantity]") or 0
            variant_type = request.POST.get(f"new_variants[{idx}][type]", "option")
            offer_label  = request.POST.get(f"new_variants[{idx}][offer_label]", "").strip()
            image        = request.FILES.get(f"new_variants[{idx}][image]")

            if sku or price:
                variant = ProductVariant.objects.create(
                    product=product,
                    variant_type=variant_type,
                    SKU=sku,
                    price=price,
                    stock_quantity=stock,
                    image=image or None,
                    offer_label=offer_label if variant_type == "offer" else "",
                )

                if variant_type == "option":
                    opt_names  = request.POST.getlist(f"new_variants[{idx}][options][][name]")
                    opt_values = request.POST.getlist(f"new_variants[{idx}][options][][value]")
                    for name, value in zip(opt_names, opt_values):
                        name, value = name.strip(), value.strip()
                        if not name or not value:
                            continue
                        option_obj, _ = ProductOption.objects.get_or_create(product=product, name=name)
                        value_obj, _  = ProductOptionValue.objects.get_or_create(option=option_obj, value=value)
                        variant.option_values.add(value_obj)

            idx += 1

        return redirect("products:products_list")

    return render(request, "dashboard/products/product_edit.html", {"product": product})