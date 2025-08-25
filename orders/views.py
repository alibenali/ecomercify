from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404, HttpResponse
from .models import Order, OrderItem, Product,  ProductVariant, ProductOptionValue
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q

class OrderListView(ListView):
    model = Order
    template_name = "dashboard/orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 20  # or 10 if you prefer

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-created_at")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status__icontains=status)

        # Search by order ID or phone number
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(status__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "")
        context["status"] = self.request.GET.get("status", "")
        return context



def order_detail_partial(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "dashboard/orders/order_detail_partial.html", {"order": order})


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
    archived = user_orders.filter(status="archived").count()
    blocked = user_orders.filter(status="blocked").count()
    return render(request, "dashboard/orders/order_status.html", {"in_progress": in_progress, "in_preparation": in_preparation, "in_dispatch": in_dispatch, "in_delivery": in_delivery, "delivered": delivered, "canceled": canceled, "archived": archived, "blocked": blocked})

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


# archive order
def archive_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "archived"
    order.save()
    # json response
    return JsonResponse({"status": "success"})

def move_to_in_progress(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "in_progress"
    order.save()
    # json response
    return JsonResponse({"status": "success"})

def send_to_sheet(request, order_id):
    pass