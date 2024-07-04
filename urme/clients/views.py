from typing import Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from shipments_app.services.paginators import get_paginator
from users.services import change_displaying_cl, get_user_settings

from .forms import Filter_clients, Pick_display_cl_clients
from .models import Clients
from .services import filters_clients, get_context_client


@login_required
def list_clients(request: HttpRequest, page: int = 1) -> HttpResponse:
    list_only = False
    order_cl, display_cl, columns, settings_user = get_user_settings(
                                                    request.user.username,
                                                    'clients')

    clients = Clients.objects.values()
    if request.method == 'POST':
        change_displaying_cl(request, settings_user, 'clients')
        return HttpResponseRedirect(reverse('clients:list'))

    is_displaying_form = Pick_display_cl_clients(data={
            'columns': [k for k, v in display_cl.items() if v]})

    if request.GET != {}:
        if 'page' in request.GET.keys():
            page = request.GET.get('page')
            list_only = request.GET.get('list_only')
        if 'reset' in request.GET.keys():
            return HttpResponseRedirect(reverse('clients:list'))
        form = Filter_clients(data=request.GET)
        if form.is_valid():
            filt = filters_clients(request.GET)
            clients = clients.filter(*filt).output_list(order_cl, display_cl)
    else:
        form = Filter_clients()
        clients = clients.output_list(order_cl, display_cl)

    clients_paginator = get_paginator(clients, list_only, page)
    if clients_paginator is None:
        return HttpResponse('')

    request_get_dict = '?' + '&'.join(f'{k}={v}' for k, v
                                      in request.GET.items() if k != 'page') + '&page='

    context = {'title': 'Клиенты',
               'clients': clients_paginator,
               'page_range': clients_paginator.paginator.get_elided_page_range(
                                                            page, on_each_side=6),
               'form_filter': form,
               'columns': columns,
               'display_form': is_displaying_form,
               'request_get': request_get_dict,
               }

    if list_only:
        return render(request, 'clients/table_clients.html', context)

    return render(request, 'clients/list_clients.html', context)


@login_required
def show_client(request: HttpRequest,
                client_id: Optional[int] = None) -> HttpResponse:
    if client_id is None:
        return HttpResponseRedirect(reverse('clients:list'))
    context = get_context_client(client_id, request.user.username)
    return render(request, 'clients/client.html', context)
