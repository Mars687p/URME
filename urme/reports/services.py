from typing import Optional

from clients.models import Clients
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from products.models import Products
from products.services import get_sum_cart
from shipments_app.models import CartProducts, Shipments
from users.models import DetailsOrganization


def get_detail_organization() -> DetailsOrganization:
    return DetailsOrganization.objects.get(fsrar_id=10000000444)


def get_carts_by_product(product: Optional[Products] = None) -> QuerySet:
    if product is None:
        return CartProducts.objects.exclude(
            shipment__condition__in=['Распроведено', 'Отклонено ЕГАИС'])
    return product.cartproducts_set.exclude(
            shipment__condition__in=['Распроведено', 'Отклонено ЕГАИС'])


def get_carts_by_shipments(shipments: QuerySet) -> QuerySet:
    return CartProducts.objects.filter(shipment_id__in=[i['id'] for i in shipments])


def get_shipments_by_cart(carts: Optional[QuerySet] = None) -> QuerySet:
    if carts is None:
        return Shipments.objects.values()
    return Shipments.objects.filter(id__in=[i['shipment_id'] for i
                                            in carts.values()]).values()


def get_shipments_by_client(client: Optional[QuerySet] = None) -> QuerySet:
    if client is None:
        return Shipments.objects.values()
    return client.shipments_set.exclude(
                condition__in=['Распроведено', 'Отклонено ЕГАИС']).values()


def get_sum_cart_by_shipment(shipments: QuerySet, carts: QuerySet) -> QuerySet:
    for shipment in shipments:
        shipment['sum_cart'] = get_sum_cart(carts.filter(shipment__id=shipment['id']))
        shipment['num'] = str(shipment['num']).rjust(6, '0')
    return shipments


def get_client(fsrar_id: Optional[int] = None) -> QuerySet:
    if fsrar_id is None:
        return Clients.objects.all()
    return get_object_or_404(Clients, fsrar_id=fsrar_id)
