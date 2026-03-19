from django.shortcuts import render, get_object_or_404, redirect
from ecom.public_decorator import public
from orders.models import Order, OrderItem
import threading
from .utils import get_client_ip, send_to_google_sheet, is_ip_blocked, block_ip, whitelist_refferer
from products.models import Product, ProductVariant
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from stores.models import Store, FacebookPixel, City
from .models import LandingPage
import datetime
from django.db.models import Prefetch, Q, Count
from staff.utils import user_can_manage_store, user_can_access_store


# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------

def get_accessible_stores(user):
    """All stores the user owns or is staff at."""
    owned = Store.objects.filter(owner=user)
    staffed = Store.objects.filter(staff__user=user)
    return (owned | staffed).distinct()


def get_landingpage_or_403(pk, user, write=False):
    """
    Fetch a landing page and check access.
    - write=False: owner or any staff can access (read/list)
    - write=True:  owner or manager staff only (create/edit/delete)
    """
    page = get_object_or_404(LandingPage, code=pk)
    check = user_can_manage_store if write else user_can_access_store
    if not check(user, page.product.store):
        raise PermissionDenied
    return page


# ---------------------------------------------------------------------------
# Public views (no auth required)
# ---------------------------------------------------------------------------

@public
def landing_page(request, code):
    IP_BLOCK = False
    REFFERER_BLOCK = False
    BLOCKED = False
    landing_page = get_object_or_404(LandingPage, code=code)
    product = landing_page.product
    store = product.store
    ip = get_client_ip(request)

    if request.method == 'POST':
        if store.block_settings["block_ip"]:
            if is_ip_blocked(ip):
                IP_BLOCK = True
                BLOCKED = True

        refferer = request.POST.get('ref', '').strip()
        if store.block_settings["block_ref"]:
            if not whitelist_refferer(refferer):
                REFFERER_BLOCK = True
                BLOCKED = True

        full_name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        province = request.POST.get('province')
        municipality = request.POST.get('municipality')

        if province:
            city = get_object_or_404(City, name=province)
            delivery_cost = city.delivery_cost
        else:
            city = None
            delivery_cost = 0

        # Check if the order is already placed in last 1 minute
        if not Order.objects.filter(phone_number=phone, created_at__range=[datetime.datetime.now() - datetime.timedelta(minutes=1), datetime.datetime.now()]).exists():
            # Resolve selected variant (offer or option)
            selected_variant = None
            offer_sku  = request.POST.get('offer_sku', '').strip()
            option_sku = request.POST.get('variant_sku', '').strip()

            if offer_sku:
                selected_variant = ProductVariant.objects.filter(
                    product=product,
                    variant_type=ProductVariant.VariantType.OFFER,
                    SKU=offer_sku,
                ).first()
            elif option_sku:
                # option_sku is "Size:SKU-L|Color:SKU-RED" — grab first matched SKU
                first_sku = option_sku.split('|')[0].split(':')[-1]
                selected_variant = ProductVariant.objects.filter(
                    product=product,
                    variant_type=ProductVariant.VariantType.OPTION,
                    SKU=first_sku,
                ).first()

            # Use variant price if one was selected, otherwise fall back to landing page price
            unit_price = selected_variant.price if selected_variant else landing_page.price

            order = Order.objects.create(
                store=store,
                full_name=full_name,
                phone_number=phone,
                address=address,
                state=province,
                city=municipality,
                delivery_cost=delivery_cost,
                http_referer=refferer,
                user_agent=request.META.get('HTTP_USER_AGENT'),
                ip_address=ip,
                status='blocked' if BLOCKED else 'in_progress',
                landing_page=landing_page,
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=selected_variant,       # None if no variant selected
                quantity=1,
                price_per_unit=unit_price,
            )

        block_ip(ip)

        if not BLOCKED:
            threading.Thread(
                target=send_to_google_sheet,
                args=(order, landing_page),
                daemon=True
            ).start()

        request.session['order_id'] = order.id
        return redirect("thankyou_page", code=landing_page.code)

# In the GET context, build variant data for the template
    cities = City.objects.filter(store=store)

    # Offer variants — flat list
    offer_variants = product.variants.filter(variant_type='offer')

    # Option variants — grouped by option name for the template
    # Structure: { "المقاس": [{"label": "L", "sku": "SKU-L"}, ...], "اللون": [...] }
    option_groups = {}
    for variant in product.variants.filter(variant_type='option').prefetch_related('option_values__option'):
        for ov in variant.option_values.all():
            group = ov.option.name
            if group not in option_groups:
                option_groups[group] = []
            option_groups[group].append({
                "label": ov.value,
                "sku": variant.SKU,
            })

    return render(request, "landing_page_2.html", {
        "landing_page": landing_page,
        "cities": cities,
        "offer_variants": offer_variants,
        "option_groups": option_groups,
    })

@public
def thankyou_page(request, code):
    try:
        order_id = request.session['order_id']
        order = Order.objects.get(id=order_id)
        del request.session['order_id']
    except Exception:
        order = None

    landing_page = get_object_or_404(LandingPage, code=code)
    store = landing_page.product.store
    return render(request, "success.html", {'store': store, 'landing_page': landing_page, 'order': order})


# ---------------------------------------------------------------------------
# Dashboard views (auth + ownership required)
# ---------------------------------------------------------------------------

@login_required
def landingpage_list(request):
    accessible_stores = get_accessible_stores(request.user)

    q = (request.GET.get("q") or "").strip()
    store_id = (request.GET.get("store") or "").strip()

    products = Product.objects.filter(store__in=accessible_stores).select_related("store")
    if store_id.isdigit():
        products = products.filter(store_id=int(store_id))

    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(store__name__icontains=q)
            | Q(landingpages__code__icontains=q)
        ).distinct()

    products = (
        products.annotate(landingpage_count=Count("landingpages", distinct=True))
        .prefetch_related(
            Prefetch(
                "landingpages",
                queryset=LandingPage.objects.order_by("-id"),
            )
        )
        .order_by("-id")
    )

    stores = accessible_stores.order_by("name")
    return render(
        request,
        "landingpages/list.html",
        {
            "products": products,
            "stores": stores,
            "q": q,
            "selected_store": int(store_id) if store_id.isdigit() else None,
        },
    )


@login_required
def landingpage_detail(request, pk):
    page = get_landingpage_or_403(pk, request.user, write=False)
    return render(request, "landingpages/detail.html", {"page": page})


@login_required
def landingpage_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    # Only owner or manager can create landing pages
    if not user_can_manage_store(request.user, product.store):
        raise PermissionDenied

    if request.method == "POST":
        landing_page = LandingPage(product=product)
        landing_page.code = request.POST.get("code")

        text_fields = [
            "custom_name", "custom_description", "custom_image",
            "custom_price", "custom_fake_price", "custom_webhook"
        ]
        bool_fields = [
            "show_state", "show_city", "show_address", "show_final_cost"
        ]

        for field in text_fields:
            if field in request.POST:
                value = request.POST[field]
                if field in ["custom_price", "custom_fake_price"] and value:
                    try:
                        value = float(value)
                    except ValueError:
                        value = None
                if value not in ["", None]:
                    if "custom_" in field:
                        if field == "custom_webhook":
                            if getattr(product.store, "sheet_webhook") != value:
                                setattr(landing_page, field, value)
                        elif getattr(product, field.replace("custom_", "")) != value:
                            setattr(landing_page, field, value)

        for field in bool_fields:
            setattr(landing_page, field, field in request.POST)

        if request.FILES.get("custom_image"):
            landing_page.custom_image = request.FILES["custom_image"]

        thank_you_html = (request.POST.get("thank_you_html") or "").strip()
        if thank_you_html:
            landing_page.thank_you_html = thank_you_html
        landing_page.save()

        pixel_ids = request.POST.getlist("pixels")
        for pixel_id in pixel_ids:
            pixel = get_object_or_404(FacebookPixel, id=pixel_id)
            landing_page.pixels.add(pixel)

        return redirect("landingpages:detail", pk=landing_page.code)

    pixels = FacebookPixel.objects.filter(store=product.store)
    return render(request, "landingpages/create.html", {"product": product, "pixels": pixels})


@login_required
def landingpage_edit(request, pk):
    landingpage = get_landingpage_or_403(pk, request.user, write=True)

    if request.method == "POST":
        text_fields = [
            "custom_name", "custom_description", "custom_image",
            "custom_price", "custom_fake_price",
            "custom_webhook", "code"
        ]
        bool_fields = [
            "show_state", "show_city", "show_address", "show_final_cost"
        ]

        for field in text_fields:
            if field in request.POST:
                value = request.POST[field]
                if value == "":
                    value = None
                if field in ["custom_price", "custom_fake_price"]:
                    if value and str(value).replace(".", "").isdigit():
                        value = float(value)
                if value == "on":
                    setattr(landingpage, field, True)
                elif value == "off":
                    setattr(landingpage, field, False)
                else:
                    if "custom_" in field:
                        if field == "custom_webhook":
                            if getattr(landingpage.product.store, 'sheet_webhook') != value:
                                setattr(landingpage, field, value)
                        elif getattr(landingpage.product, field.replace("custom_", "")) != value:
                            setattr(landingpage, field, value)
                    else:
                        setattr(landingpage, field, value)

        for field in bool_fields:
            setattr(landingpage, field, field in request.POST)

        pixels = request.POST.getlist("pixels")
        landingpage.pixels.clear()
        for pixel_id in pixels:
            pixel = get_object_or_404(FacebookPixel, id=pixel_id)
            landingpage.pixels.add(pixel)

        if request.FILES.get("custom_image"):
            landingpage.custom_image = request.FILES["custom_image"]

        thank_you_html = (request.POST.get("thank_you_html") or "").strip()
        landingpage.thank_you_html = thank_you_html or None
        landingpage.save()
        return redirect("landingpages:detail", pk=landingpage.code)

    pixels = FacebookPixel.objects.filter(store=landingpage.product.store)
    return render(request, "landingpages/edit.html", {"landingpage": landingpage, "pixels": pixels})


@login_required
def landingpage_delete(request, pk):
    landingpage = get_landingpage_or_403(pk, request.user, write=True)

    if request.method == "POST":
        landingpage.delete()
        return redirect("landingpages:list")

    return render(request, "landingpages/delete.html", {"landingpage": landingpage})