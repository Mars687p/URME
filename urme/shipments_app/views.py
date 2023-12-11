from django.shortcuts import render, HttpResponse, \
                                HttpResponseRedirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage
from shipments_app.models import Shipments
from shipments_app.forms import Filter_shipments, Shipments_data, Pick_display_cl
from shipments_app.utils import filters_ships, get_context_for_printform
from users.utils import get_user_settings, change_displaying_cl
from .utils import get_paginator


@login_required
def list_shipments(request, page=1):
    list_only = False

    order_cl, display_cl, columns, settings_user = get_user_settings(request.user.username, 
                                                      'shipments')
    if request.method == 'POST':
        change_displaying_cl(request, settings_user, 'shipments')
        return HttpResponseRedirect(reverse('shipments_app:list'))

    is_displaying_form = Pick_display_cl(data={'columns':
                            [k for k, v in display_cl.items() if v]})


    shipments = Shipments.objects.select_related('client')
    if request.GET != {}:
        if 'page' in request.GET.keys():
            page = request.GET.get('page')
            list_only = request.GET.get('list_only')

        if 'reset' in request.GET.keys(): 
            return HttpResponseRedirect(reverse('shipments_app:list'))
        form = Filter_shipments(data=request.GET)
        if form.is_valid():
            filt = filters_ships(request.GET)
            shipments = shipments.filter(*filt).output_list(order_cl, display_cl)
    else: 
        form = Filter_shipments()
        shipments = shipments.output_list(order_cl, display_cl)
    shipments_paginator = get_paginator(shipments, list_only, page)
    if shipments_paginator == None: return HttpResponse('')
    
    request_get_dict = '?' + '&'.join(f'{k}={v}' for k, v in request.GET.items() if k != 'page') + f'&page='
    context = {'title': 'Отгрузки',
               'columns': columns,
               'shipments': shipments_paginator,
               'page_range': shipments_paginator.paginator.get_elided_page_range(page, on_each_side=6),
               'form_filter': form,
               'display_form': is_displaying_form,
               'request_get': request_get_dict,
               }
    
    if list_only:
        return render(request, 'shipments_app/table_ship.html', context)
    
    return render(request, 'shipments_app/list_shipments.html', context)

@login_required
def show_shipment(request, ship_id=None):
    if ship_id == None:
        return HttpResponseRedirect(reverse('shipments_app:list'))
    shipment = get_object_or_404(Shipments.objects.select_related('client'), id=ship_id)
    transport = shipment.transports_set.first().get_values_form()
    cart_products = shipment.cartproducts_set.order_by('positions').all()
    form = Shipments_data(data=shipment.get_values_form())
    context = {'title': f'Отгрузка {shipment.num}',
               'shipment': shipment,
               'tr': transport,
               'cart': cart_products,
               'form': form,
               }
    return render(request, 'shipments_app/shipment.html', context)

#print forms
@login_required
def open_shipment_html(request, ship_id):
    context = get_context_for_printform(ship_id)
    return render(request, 'shipments_app/output_report_form.html', context)



