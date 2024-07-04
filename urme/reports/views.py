from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import HttpResponse, render
from products.services import get_products, get_sum_cart

from .services import (get_carts_by_product, get_carts_by_shipments,
                       get_client, get_detail_organization,
                       get_shipments_by_cart, get_shipments_by_client,
                       get_sum_cart_by_shipment)


@login_required
def reports_products_html(request: HttpRequest,
                          alcocode: Optional[int] = None) -> HttpResponse:
    product = get_products(alcocode)
    if alcocode is None:
        carts = get_carts_by_product()
        shipments = get_shipments_by_cart()
    else:
        carts = get_carts_by_product(product)
        shipments = get_shipments_by_cart(carts)

    organization = get_detail_organization()
    total_sum_cart = get_sum_cart(carts)
    shipments = get_sum_cart_by_shipment(shipments, carts)

    context = {
            'title': 'Отчет о продукции',
            'org': organization,
            'product': product,
            'sum_cart': total_sum_cart,
            'shipments': shipments}
    return render(request, 'reports/report_products.html', context)


@login_required
def report_clients_html(request: HttpRequest,
                        client_id: Optional[int] = None) -> HttpResponse:
    client = get_client(client_id)
    if client_id is None:
        shipments = get_shipments_by_client()
    else:
        shipments = get_shipments_by_client(client)

    cart_products = get_carts_by_shipments(shipments)
    organization = get_detail_organization()
    total_sum_cart = get_sum_cart(cart_products.all())

    shipments = get_sum_cart_by_shipment(shipments, cart_products)
    context = {
                'title': 'Клиенты',
                'org': organization,
                'client': client,
                'sum_cart': total_sum_cart,
                'shipments': shipments}
    return render(request, 'reports/report_clients.html', context)
