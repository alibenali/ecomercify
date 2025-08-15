from django.contrib import admin
from django.urls import path, include
from .views import home, landing_page, get_municipalities
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name="home"),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('orders/', include('orders.urls')),
    path('products/', include('products.urls')),
    path('stores/', include('stores.urls')),
    path('<str:sku>/', landing_page, name="landing_page"),
    path('get_municipalities/<str:city_name>/', get_municipalities, name='get_municipalities'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)