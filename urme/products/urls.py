from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('', views.list_products, name='list'),
    path('products/', views.show_product),
    path('products/<int:alcocode>/', views.show_product, name='product'),
]