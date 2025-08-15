from django.shortcuts import render
from .models import Store
# Create your views here.
def store_settings(request):
    if request.method == 'POST':
        store_name = request.POST.get('store_name')
        description = request.POST.get('description')
        sheet_webhook = request.POST.get('sheet_webhook')
        fb_pixel = request.POST.get('fb_pixel')
        fb_page = request.POST.get('fb_page')
        insta_page = request.POST.get('insta_page')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        theme_color = request.POST.get('theme_color')
        # update store
        store = Store.objects.get(owner=request.user)
        store.name = store_name
        store.description = description
        store.sheet_webhook = sheet_webhook
        store.FB_PIXEL = fb_pixel
        store.FB_PAGE = fb_page
        store.INSTA_PAGE = insta_page
        store.PHONE_NUMBER = phone_number
        store.EMAIL = email
        store.WHATSAPP = whatsapp
        store.THEME_COLOR = theme_color
        store.save()
    
    store = Store.objects.get(owner=request.user)
    return render(request, 'dashboard/stores/store_settings.html', {'store': store})