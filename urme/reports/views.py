from django.shortcuts import render
from django.shortcuts import render, HttpResponseRedirect, \
                                get_object_or_404, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from products.models import Products
from products.utils import get_sum_cart
from users.models import DetailsOrganization
from clients.models import Clients
from shipments_app.models import Shipments, CartProducts


@login_required
def reports_products_html(request, alcocode=None):
    if alcocode == None:
        product = Products.objects.all()
        carts = CartProducts.objects.exclude(shipment__condition__in=['Распроведено', 'Отклонено ЕГАИС'])
        shipments = Shipments.objects.values()
    else:
        product = get_object_or_404(Products, alcocode=alcocode)
        carts = product.cartproducts_set.exclude(shipment__condition__in=['Распроведено', 'Отклонено ЕГАИС'])
        shipments = Shipments.objects.filter(id__in=[i['shipment_id'] for i in carts.values()]).values()    

    org = DetailsOrganization.objects.get(fsrar_id=10000000444)
    sum_cart = get_sum_cart(carts)
    for shipment in shipments:
        shipment['sum_cart'] = get_sum_cart(carts.filter(shipment__id=shipment['id']))
        shipment['num'] = str(shipment['num']).rjust(6, '0')

    context = {
            'title': 'Отчет о продукции',
            'org': org,
            'product': product,
            'sum_cart': sum_cart,
            'shipments': shipments} 
    return render(request, 'reports/report_products.html', context)
    

@login_required
def report_clients_html(request, client_id=None):
    if client_id == None:
        client = Clients.objects.all()
        shipments = Shipments.objects.values()
        cart_products = CartProducts.objects.filter(shipment_id__in=[i['id'] for i in shipments])
    else:
        client = get_object_or_404(Clients, fsrar_id=client_id)
        shipments = client.shipments_set.exclude(condition__in=['Распроведено', 'Отклонено ЕГАИС']).values()
        cart_products = CartProducts.objects.filter(shipment_id__in=[i['id'] for i in shipments])


    org = DetailsOrganization.objects.get(fsrar_id=10000000444)
    sum_cart = get_sum_cart(cart_products.all())
    for shipment in shipments:
        shipment['sum_cart'] = get_sum_cart(cart_products.filter(shipment__id=shipment['id']))
        shipment['num'] = str(shipment['num']).rjust(6, '0')

    context = {'title': 'Клиенты',
            'org': org,
            'client': client,
            'sum_cart': sum_cart,
            'shipments': shipments} 
    return render(request, 'reports/report_clients.html', context)

