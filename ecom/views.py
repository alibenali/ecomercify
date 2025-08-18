
from django.shortcuts import render
from ecom.public_decorator import public
from products.models import Product
from stores.models import Store, City
from orders.models import Order, OrderItem
import os, csv, requests, threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from time import sleep

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



BLOCK_TIMEOUT = 12 * 60 * 60  # 12 hours in seconds
IP_BLOCK = False
REFFERER_BLOCK = False

def is_ip_blocked(ip):
    return cache.get(f"blocked_ip_{ip}") is not None

def block_ip(ip, timeout=BLOCK_TIMEOUT):
    cache.set(f"blocked_ip_{ip}", True, timeout)

def whitelist_refferer(refferer):
    return refferer in ['https://l.facebook.com/', 'https://www.facebook.com/', 'https://m.facebook.com/', 'https://facebook.com/', 'https://web.facebook.com/', 'https://tiktok.com/', 'https://instagram.com/', 'https://www.instagram.com/']
  
@public
def landing_page(request, sku):
    global IP_BLOCK, REFFERER_BLOCK
    
    product = Product.objects.get(SKU=sku)
    store = product.store
    ip = get_client_ip(request)

    if request.method == 'POST':

            # 🚫 Check if IP is blocked
        if is_ip_blocked(ip):
            IP_BLOCK = True
    
        refferer = request.POST.get('ref').strip()
        
        if not whitelist_refferer(refferer):
            REFFERER_BLOCK = True
        
        full_name = request.POST.get('name')
        phone = request.POST.get('phone')
        province = request.POST.get('province')
        municipality = request.POST.get('municipality')

        city = City.objects.get(name=province)

        # ✅ Save order
        order = Order.objects.create(
            store=store,
            full_name=full_name,
            phone_number=phone,
            state=province,
            city=municipality,
            delivery_cost=city.delivery_cost,
            http_referer=refferer,
            user_agent=request.META.get('HTTP_USER_AGENT'),
            ip_address=ip,
            status='blocked' if IP_BLOCK or REFFERER_BLOCK else 'in_progress'
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price_per_unit=product.price
        )

        # 🔒 Block IP for 12 hours
        block_ip(ip)

        # Fire webhook in background
        if not IP_BLOCK and not REFFERER_BLOCK:
            threading.Thread(
                target=send_to_google_sheet,
                args=(order, product, city, store),
                daemon=True
            ).start()

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
