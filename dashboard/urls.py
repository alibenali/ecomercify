from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import dashboard_home


app_name = "dashboard"

urlpatterns = [

    # Home
    path("", login_required(dashboard_home), name="home"),
    
    # # Products
    # path("products/", login_required(product_list), name="products"),


    # # Staff
    # path("staff/", login_required(staff_list), name="staff"),
]   

