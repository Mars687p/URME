from django.urls import path

from . import views

app_name = 'shipments_app'

urlpatterns = [
    path('', views.list_shipments, name='list'),
    path('shipment/', views.show_shipment),
    path('shipment/<int:ship_id>/', views.show_shipment, name='shipment'),
    path('shipment/<int:ship_id>/print/', views.open_shipment_html, name='shipment_html_form'),
]
