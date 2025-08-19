
from django.shortcuts import render, get_object_or_404, redirect
from ecom.public_decorator import public
from orders.models import Order, OrderItem
import os, csv, threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import get_client_ip, send_to_google_sheet, is_ip_blocked, block_ip, whitelist_refferer
from products.models import Product
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from stores.models import Store, FacebookPixel
from .models import LandingPage, City

@public
def landing_page(request, code):
    IP_BLOCK = False
    REFFERER_BLOCK = False
    BLOCKED = False    
    landing_page = LandingPage.objects.get(code=code)
    product = landing_page.product
    store = product.store
    ip = get_client_ip(request)

    if request.method == 'POST':

        # 🚫 Check if IP is blocked
        if store.block_settings["block_ip"]:
            if is_ip_blocked(ip):
                IP_BLOCK = True
                BLOCKED = True
    
        refferer = request.POST.get('ref').strip()
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
            city = City.objects.get(name=province)
            delivery_cost = city.delivery_cost
        else:
            city = None
            delivery_cost = 0

        # ✅ Save order
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
            landing_page=landing_page
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price_per_unit=landing_page.price
        )

        # 🔒 Block IP for 12 hours
        block_ip(ip)

        # Fire webhook in background
        if not BLOCKED:
            threading.Thread(
                target=send_to_google_sheet,
                args=(order, landing_page),
                daemon=True
            ).start()

        return render(request, "success.html", {'store': store, 'landing_page': landing_page})

    cities = City.objects.filter(store=product.store)
    return render(request, "landing_page.html", {"landing_page": landing_page, 'cities': cities})


@csrf_exempt
def get_municipalities(request, city_name):
    # get static folder path outside of the folder
    cities_path = os.path.join(settings.STATICFILES_DIRS[0], 'algeria_cities.csv')
    m = []

    with open(cities_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(reader)  # Skip the header row
        for municipality in reader:
            if municipality[4] == city_name:
                m.append(municipality[1])
    data = {'municipalities': list(m)}
    return JsonResponse(data)



def landingpage_list(request):
    pages = LandingPage.objects.all()
    store = Store.objects.get(owner=request.user)
    return render(request, "landingpages/list.html", {"pages": pages, "store": store})


def landingpage_detail(request, pk):
    page = get_object_or_404(LandingPage, code=pk)
    return render(request, "landingpages/detail.html", {"page": page})


def landingpage_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

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

        # handle text fields
        for field in text_fields:
            if field in request.POST:
                value = request.POST[field]
                if field in ["custom_price", "custom_fake_price"] and value:
                    try:
                        value = float(value)
                    except ValueError:
                        value = None

                if value not in ["", None]:
                    # only save if different from product/store default
                    if "custom_" in field:
                        if field == "custom_webhook":
                            if getattr(product.store, "sheet_webhook") != value:
                                setattr(landing_page, field, value)
                        elif getattr(product, field.replace("custom_", "")) != value:
                            setattr(landing_page, field, value)

        # handle boolean fields
        for field in bool_fields:
            setattr(landing_page, field, field in request.POST)

        landing_page.thank_you_html = request.POST.get("thank_you_html")
        landing_page.save()

        # handle pixels
        pixel_ids = request.POST.getlist("pixels")
        for pixel_id in pixel_ids:
            pixel = get_object_or_404(FacebookPixel, id=pixel_id)
            landing_page.pixels.add(pixel)

        return redirect("landingpages:detail", pk=landing_page.code)

    pixels = FacebookPixel.objects.filter(store=product.store)
    return render(request, "landingpages/create.html", {"product": product, "pixels": pixels})


# Edit landing page
def landingpage_edit(request, pk):
    landingpage = get_object_or_404(LandingPage, code=pk)

    if request.method == "POST":
        landing_page = LandingPage.objects.get(code=pk)

        text_fields = [
            "custom_name", "custom_description", "custom_image",
            "custom_price", "custom_fake_price",
            "custom_webhook"
        ]

        bool_fields = [
            "show_state", "show_city", "show_address", "show_final_cost"
        ]

        # handle text fields
        for field in text_fields:
            if field in request.POST:
                value = request.POST[field]
                # if value is float as text then convert to float
                if field == "custom_price" or field == "custom_fake_price":
                    if value.replace(".", "").isdigit():
                        value = float(value)
                if value == "on":
                    setattr(landing_page, field, True)
                elif value == "off":
                    setattr(landing_page, field, False)
                else:
                    if value == "":
                        value = None
                    if "custom_" in field:
                        if field == "custom_webhook":
                            if getattr(landing_page.product.store, 'sheet_webhook') != value:
                                setattr(landing_page, field, value)

                        elif getattr(landing_page.product,  field.replace("custom_", "")) != value:
                            setattr(landing_page, field, value)
        # handle boolean fields
        for field in bool_fields:
            setattr(landing_page, field, field in request.POST)

        pixels = request.POST.getlist("pixels")
        landing_page.pixels.clear()
        for pixel_id in pixels:
            pixel = get_object_or_404(FacebookPixel, id=pixel_id)
            landing_page.pixels.add(pixel)

        landing_page.thank_you_html = request.POST.get("thank_you_html")
        landing_page.save()
        return redirect("landingpages:detail", pk=landingpage.code)
    pixels = FacebookPixel.objects.filter(store=landingpage.product.store)
    return render(request, "landingpages/edit.html", {"landingpage": landingpage, "pixels": pixels})



# Delete landing page
def landingpage_delete(request, pk):
    landingpage = get_object_or_404(LandingPage, code=pk)

    if request.method == "POST":
        landingpage.delete()
        return redirect("landingpages:list")

    return render(request, "landingpages/delete.html", {"landingpage": landingpage})


def manage_cities(request):
    store = get_object_or_404(Store, id=1)
    cities = City.objects.filter(store=store)

    if request.method == "POST":
        if "add_city" in request.POST:
            name = request.POST.get("name")
            delivery_cost = request.POST.get("delivery_cost", 0)
            City.objects.get_or_create(
                store=store,
                name=name,
                defaults={"delivery_cost": delivery_cost}
            )
            messages.success(request, f"تمت إضافة {name}")

        if "update_city" in request.POST:
            city_id = request.POST.get("city_id")
            delivery_cost = request.POST.get("delivery_cost")
            city = get_object_or_404(City, id=city_id, store=store)
            city.delivery_cost = delivery_cost
            city.save()
            messages.success(request, f"تم تعديل تكلفة التوصيل لمدينة {city.name}")
            return redirect("landingpages:manage_cities")

        if "delete_city" in request.POST:
            city_id = request.POST.get("city_id")
            city = get_object_or_404(City, id=city_id, store=store)
            city.delete()
            messages.success(request, f"تم حذف {city.name}")
            return redirect("landingpages:manage_cities", store_id=store.id)

    return render(request, "landingpages/manage_cities.html", {"store": store, "cities": cities})