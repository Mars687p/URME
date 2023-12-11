from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('products/print', views.reports_products_html, name='print_product'),
    path('products/<int:alcocode>/print', views.reports_products_html, name='print_product'),
    path('clients/print', views.report_clients_html, name='print_client'),
    path('clients/<int:client_id>/print', views.report_clients_html, name='print_client'),
]