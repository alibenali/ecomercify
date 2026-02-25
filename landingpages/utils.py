
import requests
from django.core.cache import cache

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_to_google_sheet(order, landing_page):
    """Send order data to Google Sheet in a separate thread."""
    try:
        payload = {
            "form_name": "Landing Page Orders",
            "order_id": order.id,
            "full_name": order.full_name,
            "phone": order.phone_number,
            "province": order.state,
            "municipality": order.city,
            "product": landing_page.name,
            "price": landing_page.price,
            "delivery_cost": order.delivery_cost,
            "total": landing_page.price + order.delivery_cost,
            "e_gs_SheetName": "Orders",  # Optional sheet name
            "e_gs_order": "order_id,full_name,phone,province,municipality,product,price,delivery_cost,total"
        }
        requests.post(landing_page.webhook, data=payload, timeout=5)
    except requests.RequestException as e:
        print(f"Google Sheet webhook failed: {e}")

def is_ip_blocked(ip):
    return cache.get(f"blocked_ip_{ip}") is not None

def block_ip(ip, timeout=12 * 60 * 60):
    cache.set(f"blocked_ip_{ip}", True, timeout)

def whitelist_refferer(refferer):
    return refferer in ['https://l.facebook.com/', 'https://www.facebook.com/', 'https://m.facebook.com/', 'https://facebook.com/', 'https://web.facebook.com/', 'https://tiktok.com/', 'https://instagram.com/', 'https://www.instagram.com/']
  