from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404, HttpResponse
from .models import Order, OrderItem, Product, ProductVariant
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string

class OrderListView(ListView):
    model = Order
    template_name = "dashboard/orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10  # Adjust pagination as needed

    def get_queryset(self):
        return Order.objects.all().order_by("-created_at")

def order_detail_partial(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    variants = ProductVariant.objects.select_related('product').all()  # or filtered
    return render(request, "dashboard/orders/order_detail_partial.html", {"order": order, "variants": variants})


@csrf_exempt
def update_order_item(request, item_id):
    # make a delay
    import time
    time.sleep(2)

    item = get_object_or_404(OrderItem, id=item_id)

    if request.method == "POST":
        # update price if price_per_unit is changed and quantity if it's changed
        if "price_per_unit" in request.POST:
            new_price = request.POST.get("price_per_unit")
            item.price_per_unit = float(new_price)
        
        if "quantity" in request.POST:
            new_quantity = request.POST.get("quantity")
            item.quantity = int(new_quantity)

        if "delivery_cost" in request.POST:
            new_delivery_cost = request.POST.get("delivery_cost")
            item.delivery_cost = float(new_delivery_cost)

        if "discount" in request.POST:
            new_discount = request.POST.get("discount")
            item.discount = float(new_discount)

        item.save()
        order = get_object_or_404(Order, id=item.order.id)
        return render(request, "dashboard/orders/order_detail_partial.html", {"order": order})

@csrf_exempt
def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        if "delivery_cost" in request.POST:
            new_delivery_cost = request.POST.get("delivery_cost")
            order.delivery_cost = float(new_delivery_cost)

        if "discount" in request.POST:
            new_discount = request.POST.get("discount")
            order.discount = float(new_discount)

        order.save()
        return render(request, "dashboard/orders/order_detail_partial.html", {"order": order})
    
@csrf_exempt
def order_status(request):
    user= request.user
    user_stores = user.stores.all()
    user_orders = Order.objects.filter(store__in=user_stores)
    in_progress = user_orders.filter(status="in_progress").count()
    in_preparation = user_orders.filter(status="in_preparation").count()
    in_dispatch = user_orders.filter(status="in_dispatch").count()
    in_delivery = user_orders.filter(status="in_delivery").count()
    delivered = user_orders.filter(status="delivered").count()
    canceled = user_orders.filter(status="canceled").count()
    return render(request, "dashboard/orders/order_status.html", {"in_progress": in_progress, "in_preparation": in_preparation, "in_dispatch": in_dispatch, "in_delivery": in_delivery, "delivered": delivered, "canceled": canceled})

@csrf_exempt
def delete_order_item(request, item_id):
    order_item = OrderItem.objects.get(id=item_id)
    order = Order.objects.get(id=order_item.order.id)
    order_item.delete()
    return HttpResponseRedirect(reverse("order_detail", args=[order.id]))


@csrf_exempt
def order_client_info(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'dashboard/orders/order_client_info.html', {'order':order})

@csrf_exempt
def edit_client_info(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == "POST":
        order.full_name = request.POST.get("full_name")
        order.phone_number = request.POST.get("phone_number")
        order.address = request.POST.get("address")
        order.city = request.POST.get('city')
        order.state = request.POST.get('state')
        order.delivery_method = request.POST.get('delivery_method')
        order.save()
        return render(request, 'dashboard/orders/order_client_info.html', {'order':order})

    return render(request, 'dashboard/orders/edit_client_info.html', {'order':order})

