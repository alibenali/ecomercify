from django.urls import path
from . import views as landingpages
from . import views

app_name = "landingpages"

urlpatterns = [

    path("get_municipalities/<str:city_name>/", landingpages.get_municipalities, name='get_municipalities'),
    path("manage_cities/", views.manage_cities, name="manage_cities"),
    path("landing-pages/", views.landingpage_list, name="list"),
    path("create/<product_id>/", views.landingpage_create, name="create"),
    path("<str:pk>/", views.landingpage_detail, name="detail"),
    path("<int:pk>/edit/", views.landingpage_edit, name="edit"),
    path("<int:pk>/delete/", views.landingpage_delete, name="delete"),

]

