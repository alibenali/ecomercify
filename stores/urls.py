from django.urls import path
from . import views

app_name = 'stores'

urlpatterns = [
    path('', views.store_list, name='list'),
    path('manage/create/', views.store_create, name='create'),
    path('manage/<int:pk>/edit/', views.store_update, name='edit'),
    path('manage/<int:pk>/delete/', views.store_delete, name='delete'),
    path("get_municipalities/<str:city_name>/", views.get_municipalities, name='get_municipalities'),
    path("manage_cities/", views.manage_cities, name="manage_cities"),
]