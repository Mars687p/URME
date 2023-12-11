from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main_page.urls')),
    path('login/', include('users.urls')),
    path('shipments/', include('shipments_app.urls')),
    path('clients/', include('clients.urls')),
    path('products/', include('products.urls')),
    path('reports/', include('reports.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
]
