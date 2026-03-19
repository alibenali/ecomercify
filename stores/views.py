from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Store, FacebookPixel, City
from .forms import StoreForm
from django.views.decorators.csrf import csrf_exempt
import os, csv
from django.http import JsonResponse
from django.conf import settings


@login_required
def store_list(request):
    stores = Store.objects.filter(owner=request.user).order_by("-created_at")
    return render(
        request,
        "dashboard/stores/store_list.html",
        {
            "stores": stores,
        },
    )


@login_required
def store_create(request):
    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user

            # Security checkboxes
            block_ref = request.POST.get("block_ref") == "on"
            block_ip = request.POST.get("block_ip") == "on"
            store.block_settings = {
                "block_ref": block_ref,
                "block_ip": block_ip,
            }

            # Save store first to have an ID for pixels
            store.save()

            # Handle multiple Facebook Pixels
            fb_pixels = request.POST.getlist("fb_pixels")
            for pixel_code in fb_pixels:
                if pixel_code.strip():
                    FacebookPixel.objects.create(store=store, pixel_code=pixel_code.strip())

            messages.success(request, "Store created successfully.")
            return redirect("stores:list")
    else:
        form = StoreForm()

    return render(
        request,
        "dashboard/stores/store_form.html",
        {
            "form": form,
            "page_title": "Create Store",
        },
    )


@login_required
def store_update(request, pk):
    store = get_object_or_404(Store, pk=pk, owner=request.user)

    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            store = form.save(commit=False)

            # Security checkboxes
            block_ref = request.POST.get("block_ref") == "on"
            block_ip = request.POST.get("block_ip") == "on"
            store.block_settings = {
                "block_ref": block_ref,
                "block_ip": block_ip,
            }

            store.save()

            # Handle multiple Facebook Pixels
            fb_pixels = request.POST.getlist("fb_pixels")

            # Clear old pixels for this store
            FacebookPixel.objects.filter(store=store).delete()

            # Save new ones
            for pixel_code in fb_pixels:
                if pixel_code.strip():
                    FacebookPixel.objects.create(store=store, pixel_code=pixel_code.strip())

            messages.success(request, "Store updated successfully.")
            return redirect("stores:list")
    else:
        form = StoreForm(instance=store)

    return render(
        request,
        "dashboard/stores/store_form.html",
        {
            "form": form,
            "store": store,
            "page_title": "Edit Store",
        },
    )


@login_required
def store_delete(request, pk):
    store = get_object_or_404(Store, pk=pk, owner=request.user)

    if request.method == "POST":
        store.delete()
        messages.success(request, "Store deleted successfully.")
        return redirect("stores:list")

    return render(
        request,
        "dashboard/stores/store_confirm_delete.html",
        {
            "store": store,
        },
    )


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



def manage_cities(request):
    user = request.user
    store = get_object_or_404(Store, owner=user)
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
            return redirect("stores:manage_cities")

        if "delete_city" in request.POST:
            city_id = request.POST.get("city_id")
            city = get_object_or_404(City, id=city_id, store=store)
            city.delete()
            messages.success(request, f"تم حذف {city.name}")
            return redirect("stores:manage_cities", store_id=store.id)

    return render(request, "dashboard/stores/manage_cities.html", {"store": store, "cities": cities})