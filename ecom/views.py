
from django.shortcuts import render
from ecom.public_decorator import public
from products.models import Product
from stores.models import Store, City
from orders.models import Order, OrderItem
import os
import csv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@public
def home(request):
    return render(request, "home.html")

@public
def landing_page(request, sku):
    product = Product.objects.get(SKU=sku)
    if request.method == 'POST':
        form = request.POST
        full_name = form.get('name')
        phone = form.get('phone')
        province = form.get('province')
        municipality = form.get('municipality')
        phone = form.get('phone')
        store = product.store
        city = City.objects.get(name=province)
        order = Order.objects.create(store =store,full_name=full_name, phone_number=phone, state=province, city=municipality, delivery_cost=city.delivery_cost)
        order.save()
        order_item = OrderItem.objects.create(order=order, product=product, quantity=1, price_per_unit=product.price)
        order_item.save()
        return render(request, "success.html")
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
