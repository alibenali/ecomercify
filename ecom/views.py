
from django.shortcuts import render
from ecom.public_decorator import public
from products.models import Product
from stores.models import Store
from orders.models import Order, OrderItem
import os, csv, requests, threading
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from time import sleep
from landingpages.models import LandingPage, City


@csrf_exempt
def upload_paste_image(request):
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]
        base, ext = os.path.splitext(upload.name)
        filename = upload.name
        counter = 1

        # loop until we find a non-existing filename
        while os.path.exists(os.path.join(settings.MEDIA_ROOT, filename)):
            filename = f"{base}_{counter}{ext}"
            counter += 1

        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        with open(file_path, "wb+") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)

        return JsonResponse({
            "uploaded": 1,
            "fileName": filename,
            "url": settings.MEDIA_URL + filename
        })

    return JsonResponse({"uploaded": 0, "error": {"message": "Upload failed"}})

@csrf_exempt
def upload_image(request):
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]
        base, ext = os.path.splitext(upload.name)
        filename = upload.name
        counter = 1

        # Ensure unique filename
        while os.path.exists(os.path.join(settings.MEDIA_ROOT, filename)):
            filename = f"{base}_{counter}{ext}"
            counter += 1

        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        with open(file_path, "wb+") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)

        url = settings.MEDIA_URL + filename
        callback = request.GET.get("CKEditorFuncNum")  # 👈 CKEditor sends this

        return HttpResponse(
            f"<script>window.parent.CKEDITOR.tools.callFunction({callback}, '{url}', '');</script>"
        )

    return HttpResponse(
        "<script>alert('Upload failed');</script>"
    )

@public
def home(request):
    return render(request, "home.html")


