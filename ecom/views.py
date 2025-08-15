
from django.shortcuts import render
from ecom.public_decorator import public
from products.models import Product
from stores.models import Store, City
from orders.models import Order, OrderItem
import os, csv, requests, threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@public
def home(request):
    return render(request, "home.html")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_to_google_sheet(order, product, city, store):
    """Send order data to Google Sheet in a separate thread."""
    try:
        payload = {
            "form_name": "Landing Page Orders",
            "order_id": order.id,
            "full_name": order.full_name,
            "phone": order.phone_number,
            "province": order.state,
            "municipality": order.city,
            "product": product.name,
            "price": product.price,
            "delivery_cost": city.delivery_cost,
            "total": product.price + city.delivery_cost,
            "e_gs_SheetName": "Orders",  # Optional sheet name
            "e_gs_order": "order_id,full_name,phone,province,municipality,product,price,delivery_cost,total"
        }
        requests.post(store.sheet_webhook, data=payload, timeout=5)
    except requests.RequestException as e:
        print(f"Google Sheet webhook failed: {e}")

@public
def landing_page(request, sku):
    product = Product.objects.get(SKU=sku)

    if request.method == 'POST':
        refferer = request.POST.get('ref')
        full_name = request.POST.get('name')
        phone = request.POST.get('phone')
        province = request.POST.get('province')
        municipality = request.POST.get('municipality')

        store = product.store
        city = City.objects.get(name=province)

        # Save order to database
        order = Order.objects.create(
            store=store,
            full_name=full_name,
            phone_number=phone,
            state=province,
            city=municipality,
            delivery_cost=city.delivery_cost,
            http_referer=refferer,
            user_agent=request.META.get('HTTP_USER_AGENT'),
            ip_address=get_client_ip(request)
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price_per_unit=product.price
        )

        # Fire webhook in a separate thread
        threading.Thread(
            target=send_to_google_sheet,
            args=(order, product, city, store),
            daemon=True
        ).start()

        # Return response immediately
        return render(request, "success.html", {'store': store})

    cities = City.objects.filter(store=product.store)
    return render(request, "landing_page.html", {"product": product, 'cities': cities})


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
