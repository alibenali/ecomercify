from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from .models import Order, OrderItem, StatusHistory
from products.models import ProductVariant
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from landingpages.utils import send_to_google_sheet
from landingpages.models import LandingPage
from stores.models import Store
from django.views.decorators.csrf import csrf_exempt

def user_can_access_store(user, store):
    """Returns True if the user owns the store or is a staff member of it."""
    if store.owner == user:
        return True
    return store.staff.filter(user=user).exists()


def get_order_or_403(order_id, user):
    order = get_object_or_404(Order, id=order_id)
    if not user_can_access_store(user, order.store):
        raise PermissionDenied
    return order


def get_order_item_or_403(item_id, user):
    item = get_object_or_404(OrderItem, id=item_id)
    if not user_can_access_store(user, item.order.store):
        raise PermissionDenied
    return item


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "dashboard/orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Stores the user owns
        owned_stores = Store.objects.filter(owner=user)
        # Stores the user is staff at
        staff_stores = Store.objects.filter(staff__user=user)
        # Combine both without duplicates
        accessible_stores = (owned_stores | staff_stores).distinct()

        queryset = Order.objects.filter(
            store__in=accessible_stores
        ).order_by("-created_at")

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status__icontains=status)

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


@login_required
def order_detail_partial(request, order_id):
    order = get_order_or_403(order_id, request.user)
    products = order.store.products.prefetch_related("variants").order_by("name")
    return render(
        request,
        "dashboard/orders/order_detail_partial.html",
        {"order": order, "products": products},
    )


@login_required
@csrf_exempt
def add_order_item(request, order_id):
    order = get_order_or_403(order_id, request.user)
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    product_variant = request.POST.get("product_variant", "").strip()
    quantity = request.POST.get("quantity", 1)
    price_per_unit = request.POST.get("price_per_unit")

    if not product_variant:
        return JsonResponse({"error": "Product is required"}, status=400)

    product = None
    variant = None
    if product_variant.startswith("product_"):
        product_id = product_variant.replace("product_", "")
        product = get_object_or_404(order.store.products, id=product_id)
        if not price_per_unit:
            price_per_unit = str(product.price)
    elif product_variant.startswith("variant_"):
        variant_id = product_variant.replace("variant_", "")
        variant = get_object_or_404(
            ProductVariant, id=variant_id, product__store=order.store
        )
        product = variant.product
        if not price_per_unit:
            price_per_unit = str(variant.price)
    else:
        return JsonResponse({"error": "Invalid product selection"}, status=400)

    try:
        quantity = int(quantity)
        price_per_unit = float(price_per_unit)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid quantity or price"}, status=400)

    if quantity < 1:
        return JsonResponse({"error": "Quantity must be at least 1"}, status=400)

    order_item = OrderItem.objects.create(
        order=order,
        product=product,
        variant=variant,
        quantity=quantity,
        price_per_unit=price_per_unit,
    )

    # History: item added
    StatusHistory.objects.create(
        order=order,
        order_item=order_item,
        action=StatusHistory.Action.ITEM_ADD,
        field_name="item",
        previous_value="",
        new_value=f"{order_item.get_name()} x {order_item.quantity}",
        changed_by=request.user,
    )
    return render(
        request,
        "dashboard/orders/order_detail_partial.html",
        {"order": order, "products": order.store.products.prefetch_related("variants").order_by("name")},
    )


@login_required
@csrf_exempt
def update_order_item(request, item_id):
    import time
    time.sleep(2)

    item = get_order_item_or_403(item_id, request.user)

    if request.method == "POST":
        changes = []

        if "price_per_unit" in request.POST:
            old = item.price_per_unit
            new = float(request.POST.get("price_per_unit"))
            if old != new:
                item.price_per_unit = new
                changes.append(("price_per_unit", old, new))

        if "quantity" in request.POST:
            old = item.quantity
            new = int(request.POST.get("quantity"))
            if old != new:
                item.quantity = new
                changes.append(("quantity", old, new))

        # Save once after applying changes
        if changes:
            item.save()
            for field_name, old, new in changes:
                StatusHistory.objects.create(
                    order=item.order,
                    order_item=item,
                    action=StatusHistory.Action.ITEM_UPDATE,
                    field_name=field_name,
                    previous_value=str(old),
                    new_value=str(new),
                    changed_by=request.user,
                )

        order = item.order
        products = order.store.products.prefetch_related("variants").order_by("name")
        return render(
            request,
            "dashboard/orders/order_detail_partial.html",
            {"order": order, "products": products},
        )


@login_required
@csrf_exempt
def update_order(request, order_id):
    order = get_order_or_403(order_id, request.user)

    if request.method == "POST":
        changes = []

        if "delivery_cost" in request.POST:
            old = order.delivery_cost
            new = float(request.POST.get("delivery_cost"))
            if old != new:
                order.delivery_cost = new
                changes.append(("delivery_cost", old, new))

        if "discount" in request.POST:
            old = order.discount
            new = float(request.POST.get("discount"))
            if old != new:
                order.discount = new
                changes.append(("discount", old, new))

        if changes:
            order.save()
            for field_name, old, new in changes:
                StatusHistory.objects.create(
                    order=order,
                    action=StatusHistory.Action.ORDER_UPDATE,
                    field_name=field_name,
                    previous_value=str(old),
                    new_value=str(new),
                    changed_by=request.user,
                )

        products = order.store.products.prefetch_related("variants").order_by("name")
        return render(
            request,
            "dashboard/orders/order_detail_partial.html",
            {"order": order, "products": products},
        )


@login_required
def order_status(request):
    user = request.user
    owned_stores = Store.objects.filter(owner=user)
    staff_stores = Store.objects.filter(staff__user=user)
    accessible_stores = (owned_stores | staff_stores).distinct()

    user_orders = Order.objects.filter(store__in=accessible_stores)

    status_counts = {
        status: user_orders.filter(status=status).count()
        for status in [
            "in_progress", "in_preparation", "in_dispatch",
            "in_delivery", "delivered", "canceled", "archived", "blocked"
        ]
    }
    return render(request, "dashboard/orders/order_status.html", status_counts)


@login_required
@csrf_exempt
def delete_order_item(request, item_id):
    item = get_order_item_or_403(item_id, request.user)
    order = item.order

    # Capture info before deleting
    item_summary = f"{item.get_name()} x {item.quantity}"
    item_id_value = item.id
    item.delete()

    StatusHistory.objects.create(
        order=order,
        order_item=None,
        action=StatusHistory.Action.ITEM_DELETE,
        field_name="item",
        previous_value=item_summary,
        new_value=f"deleted (id={item_id_value})",
        changed_by=request.user,
    )
    products = order.store.products.prefetch_related("variants").order_by("name")
    return render(
        request,
        "dashboard/orders/order_detail_partial.html",
        {"order": order, "products": products},
    )


@login_required
def order_client_info(request, order_id):
    order = get_order_or_403(order_id, request.user)
    return render(request, "dashboard/orders/order_client_info.html", {"order": order})


@login_required
@csrf_exempt
def edit_client_info(request, order_id):
    order = get_order_or_403(order_id, request.user)

    if request.method == "POST":
        changes = []

        if "full_name" in request.POST:
            old = order.full_name
            new = request.POST.get("full_name")
            if old != new:
                order.full_name = new
                changes.append(("full_name", old, new))

        if "phone_number" in request.POST:
            old = order.phone_number
            new = request.POST.get("phone_number")
            if old != new:
                order.phone_number = new
                changes.append(("phone_number", old, new))

        if "address" in request.POST:
            old = order.address
            new = request.POST.get("address")
            if old != new:
                order.address = new
                changes.append(("address", old, new))

        if "city" in request.POST:
            old = order.city
            new = request.POST.get("city")
            if old != new:
                order.city = new
                changes.append(("city", old, new))

        if "state" in request.POST:
            old = order.state
            new = request.POST.get("state")
            if old != new:
                order.state = new
                changes.append(("state", old, new))

        if "delivery_method" in request.POST:
            old = order.delivery_method
            new = request.POST.get("delivery_method")
            if old != new:
                order.delivery_method = new
                changes.append(("delivery_method", old, new))

        if changes:
            order.save()
            for field_name, old, new in changes:
                StatusHistory.objects.create(
                    order=order,
                    action=StatusHistory.Action.ORDER_UPDATE,
                    field_name=field_name,
                    previous_value=str(old) if old is not None else "",
                    new_value=str(new) if new is not None else "",
                    changed_by=request.user,
                )

        return render(request, "dashboard/orders/order_client_info.html", {"order": order})

    return render(request, "dashboard/orders/edit_client_info.html", {"order": order})


@login_required
def archive_order(request, order_id):
    order = get_order_or_403(order_id, request.user)
    previous_status = order.status
    order.status = "archived"
    order.save()

    StatusHistory.objects.create(
        order=order,
        action=StatusHistory.Action.STATUS_CHANGE,
        field_name="status",
        previous_status=previous_status,
        new_status=order.status,
        previous_value=previous_status,
        new_value=order.status,
        changed_by=request.user,
    )
    return JsonResponse({"status": "success"})


@login_required
def move_to_in_progress(request, order_id):
    order = get_order_or_403(order_id, request.user)
    previous_status = order.status
    order.status = "in_progress"
    order.save()

    StatusHistory.objects.create(
        order=order,
        action=StatusHistory.Action.STATUS_CHANGE,
        field_name="status",
        previous_status=previous_status,
        new_status=order.status,
        previous_value=previous_status,
        new_value=order.status,
        changed_by=request.user,
    )
    return JsonResponse({"status": "success"})


@login_required
def send_to_sheet(request, order_id):
    order = get_order_or_403(order_id, request.user)
    landing_page = get_object_or_404(LandingPage, code=order.landing_page.code)
    send_to_google_sheet(order, landing_page)
    return JsonResponse({"status": "success"})