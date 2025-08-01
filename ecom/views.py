
from django.shortcuts import render
from ecom.public_decorator import public

@public
def home(request):
    return render(request, "home.html")