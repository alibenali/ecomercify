
from django.shortcuts import render
from ecom.public_decorator import public
from products.models import Product
from stores.models import Store
from orders.models import Order, OrderItem
import os, csv, requests, threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from time import sleep
from landingpages.models import LandingPage, City

@public
def home(request):
    return render(request, "home.html")
