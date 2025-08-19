from django.contrib import admin
from django.urls import path, include
from .views import home
from landingpages.views import landing_page, thankyou_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name="home"),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('orders/', include('orders.urls')),
    path('landingpages/', include('landingpages.urls')),
    path('products/', include('products.urls')),
    path('stores/', include('stores.urls')),
    path('thankyou/', thankyou_page, name="thankyou_page"),
    path('<str:code>/', landing_page, name="landing_page"),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)