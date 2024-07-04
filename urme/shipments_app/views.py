from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from shipments_app.forms import Filter_shipments, Pick_display_cl
from shipments_app.services.filters import filters_ships
from users.services import change_displaying_cl, get_user_settings

from .services.objects import (get_context_show_shipment,
                               get_shipments_with_client)
from .services.paginators import get_paginator
from .services.print_forms import get_context_for_printform


@login_required
def list_shipments(request: HttpRequest, page: int = 1) -> HttpResponse:
    list_only = False

    order_cl, display_cl, columns, settings_user = get_user_settings(
                                                        request.user.username,
                                                        'shipments')
    if request.method == 'POST':
        change_displaying_cl(request, settings_user, 'shipments')
        return HttpResponseRedirect(reverse('shipments_app:list'))

    is_displaying_form = Pick_display_cl(data={
                        'columns': [k for k, v in display_cl.items() if v]})

    shipments = get_shipments_with_client()
    if request.GET != {}:
        if 'reset' in request.GET.keys():
            return HttpResponseRedirect(reverse('shipments_app:list'))

        if 'page' in request.GET.keys():
            page = request.GET.get('page')
            list_only = request.GET.get('list_only')

        form = Filter_shipments(data=request.GET)
        if form.is_valid():
            filt = filters_ships(request.GET)
            shipments = shipments.filter(*filt).output_list(order_cl, display_cl)
    else:
        form = Filter_shipments()
        shipments = shipments.output_list(order_cl, display_cl)

    shipments_paginator = get_paginator(shipments, list_only, page)
    if shipments_paginator is None:
        return HttpResponse('')

    filters_for_pagination = '?' + '&'.join(
            f'{k}={v}' for k, v in request.GET.items() if k != 'page') + '&page='
    context = {
        'title': 'Отгрузки',
        'columns': columns,
        'shipments': shipments_paginator,
        'form_filter': form,
        'display_form': is_displaying_form,
        'request_get': filters_for_pagination,
        'page_range': shipments_paginator.paginator.get_elided_page_range(
                                                page,
                                                on_each_side=6),
               }

    if list_only:
        return render(request, 'shipments_app/table_ship.html', context)
    return render(request, 'shipments_app/list_shipments.html', context)


@login_required
def show_shipment(request: HttpRequest,
                  ship_id: Optional[int] = None) -> HttpResponse:
    if ship_id is None:
        return HttpResponseRedirect(reverse('shipments_app:list'))
    context = get_context_show_shipment(ship_id)
    return render(request, 'shipments_app/shipment.html', context)


@login_required
def open_shipment_html(request: HttpRequest, ship_id: int) -> HttpResponse:
    context = get_context_for_printform(ship_id)
    return render(request, 'shipments_app/output_report_form.html', context)
