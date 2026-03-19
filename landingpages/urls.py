from django.urls import path
from . import views as landingpages
from . import views

app_name = "landingpages"

urlpatterns = [
    path("landing-pages/", views.landingpage_list, name="list"),
    path("create/<product_id>/", views.landingpage_create, name="create"),
    path("<str:pk>/", views.landingpage_detail, name="detail"),
    path("<str:pk>/edit/", views.landingpage_edit, name="edit"),
    path("<str:pk>/delete/", views.landingpage_delete, name="delete"),

]

