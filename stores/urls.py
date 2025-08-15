from django.urls import path
from . import views

app_name = 'stores'

urlpatterns = [
    path('', views.store_settings, name='settings'),
]