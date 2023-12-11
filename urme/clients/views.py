from django.shortcuts import render, HttpResponse, HttpResponseRedirect,\
                             get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Clients
from .forms import Filter_clients, Pick_display_cl_clients, Select_date
from .utils import filters_clients

from shipments_app.models import CartProducts
from products.utils import get_sum_cart
from shipments_app.utils import get_paginator
from users.utils import get_user_settings, change_displaying_cl
from users.models import DetailsOrganization


@login_required
def list_clients(request, page=1):
    list_only = False
    order_cl, display_cl, columns, settings_user = get_user_settings(request.user.username, 
                                                    'clients')

    clients = Clients.objects.values()
    if request.method == 'POST':
        change_displaying_cl(request, settings_user, 'clients')
        return HttpResponseRedirect(reverse('clients:list'))
    
    is_displaying_form = Pick_display_cl_clients(data={'columns':
                        [k for k, v in display_cl.items() if v]})

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
    if clients_paginator == None: return HttpResponse('')

    request_get_dict = '?' + '&'.join(f'{k}={v}' for k, v in request.GET.items() if k != 'page') + f'&page='

    context = {'title': 'Клиенты',
               'clients': clients_paginator,
               'page_range': clients_paginator.paginator.get_elided_page_range(page, on_each_side=6),
               'form_filter': form,
               'columns': columns,
               'display_form': is_displaying_form,
               'request_get': request_get_dict,
               }
        
    if list_only:
        return render(request, 'clients/table_clients.html', context)
    
    return render(request, 'clients/list_clients.html', context)

@login_required
def show_client(request, client_id=None):
    if client_id == None:
        return HttpResponseRedirect(reverse('clients:list'))
    
    order_cl, display_cl, columns, _ = get_user_settings(request.user.username, 
                                                    'shipments')
    client = get_object_or_404(Clients, fsrar_id=client_id)
    shipments = client.shipments_set.exclude(condition__in=['Распроведено', 'Отклонено ЕГАИС']).output_list(order_cl, display_cl)
    carts_client = CartProducts.objects.filter(shipment_id__in=[i['id'] for i in shipments])

    statistics_per_month = get_sum_cart(carts_client.filter(
                                shipment_id__in=[i['id'] for i in shipments.ships_per_month()]))
    statistics_per_year = get_sum_cart(carts_client.filter(
                                    shipment_id__in=[i['id'] for i in shipments.ships_per_year()]))
    
    form_date = Select_date(data={'date_select': 'month'})

    context = {'title': client.full_name,
               'client': client,
               'shipments': shipments,
               'columns': columns,
               'statistics_per_month': statistics_per_month,
               'statistics_per_year': statistics_per_year,
               'form_date': form_date,
               }
    return render(request, 'clients/client.html', context)


