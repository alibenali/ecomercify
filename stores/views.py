from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Store, FacebookPixel


@login_required
def store_settings(request):
    store = Store.objects.get(owner=request.user)

    if request.method == 'POST':
        # Base fields
        store.name = request.POST.get('store_name')
        store.description = request.POST.get('description')
        store.sheet_webhook = request.POST.get('sheet_webhook')
        store.FB_PAGE = request.POST.get('fb_page')
        store.INSTA_PAGE = request.POST.get('insta_page')
        store.PHONE_NUMBER = request.POST.get('phone_number')
        store.EMAIL = request.POST.get('email')
        store.WHATSAPP = request.POST.get('whatsapp')
        store.THEME_COLOR = request.POST.get('theme_color')

        # Security checkboxes
        block_ref = request.POST.get("block_ref") == "on"
        block_ip = request.POST.get("block_ip") == "on"
        store.block_settings = {
            "block_ref": block_ref,
            "block_ip": block_ip
        }

        # Save store updates first
        store.save()

        # Handle multiple Facebook Pixels
        fb_pixels = request.POST.getlist("fb_pixels")

        # Clear old pixels for this store
        FacebookPixel.objects.filter(store=store).delete()

        # Save new ones
        for pixel_code in fb_pixels:
            if pixel_code.strip():  # ignore empty textareas
                FacebookPixel.objects.create(store=store, pixel_code=pixel_code.strip())

        return redirect("stores:settings")  # redirect after save

    return render(request, "dashboard/stores/store_settings.html", {"store": store})
