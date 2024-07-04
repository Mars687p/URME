from typing import Any, Dict

from django.db.models import Q
from django.shortcuts import get_object_or_404
from products.services import get_sum_cart
from shipments_app.models import CartProducts
from users.services import get_user_settings

from .forms import Select_date
from .models import Clients


def filters_clients(request_get: dict) -> list:
    filters = []
    if request_get != {}:
        for filter in request_get:
            if len(request_get[filter]) > 0:
                if filter == 'fsrar_id':
                    fsrar_id = int(request_get[filter])
                    filters.append(Q(fsrar_id__icontains=fsrar_id))
                if filter == 'client':
                    filters.append(Q(full_name__icontains=request_get[filter]))
                if filter == 'inn':
                    filters.append(Q(inn__icontains=request_get[filter]))
                if filter == 'kpp':
                    filters.append(Q(kpp__icontains=request_get[filter]))
    return filters


def get_context_client(client_id: int, username: str) -> Dict[str, Any]:

    order_cl, display_cl, columns, _ = get_user_settings(username,
                                                         'shipments')

    client = get_object_or_404(Clients, fsrar_id=client_id)
    shipments = client.shipments_set.exclude(
            condition__in=['Распроведено', 'Отклонено ЕГАИС']).output_list(order_cl, display_cl)
    carts_client = CartProducts.objects.filter(shipment_id__in=[i['id'] for i in shipments])

    statistics_per_month = get_sum_cart(carts_client.filter(
                                shipment_id__in=[i['id'] for i in shipments.ships_per_month()]))
    statistics_per_year = get_sum_cart(carts_client.filter(
                                shipment_id__in=[i['id'] for i in shipments.ships_per_year()]))

    form_date = Select_date(data={'date_select': 'month'})

    return {
            'title': client.full_name,
            'client': client,
            'shipments': shipments,
            'columns': columns,
            'statistics_per_month': statistics_per_month,
            'statistics_per_year': statistics_per_year,
            'form_date': form_date,
               }
