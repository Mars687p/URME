from django.urls import path
from . import views


app_name = 'clients'

urlpatterns = [
    path('', views.list_clients, name='list'),
    path('client/', views.show_client),
    path('client/<int:client_id>/', views.show_client, name='client'),
]
