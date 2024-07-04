from typing import Any, Dict

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from shipments_app.forms import Shipments_data
from shipments_app.models import Shipments


def get_context_show_shipment(ship_id: int) -> Dict[str, Any]:
    shipment: Shipments = get_object_or_404(Shipments.objects.select_related('client'),
                                            id=ship_id)
    transport = shipment.transports_set.first().get_values_form()
    cart_products = shipment.cartproducts_set.order_by('positions').all()
    form = Shipments_data(data=shipment.get_values_form())
    return {'title': f'Отгрузка {shipment.num}',
            'shipment': shipment,
            'tr': transport,
            'cart': cart_products,
            'form': form,
            }


def get_shipments_with_client() -> QuerySet:
    return Shipments.objects.select_related('client')
