from typing import Optional

from clients.forms import Select_date
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from shipments_app.models import Shipments
from shipments_app.services.paginators import get_paginator
from users.services import change_displaying_cl, get_user_settings

from .forms import Filter_products, Pick_display_cl_products
from .models import Products
from .services import filter_products, get_sum_cart


@login_required
def list_products(request: HttpRequest,
                  page: int = 1) -> HttpResponse | HttpResponseRedirect:
    list_only = False
    order_cl, display_cl, columns, settings_user = get_user_settings(
                                                    request.user.username,
                                                    'products')

    if request.method == 'POST':
        change_displaying_cl(request, settings_user, 'products')
        return HttpResponseRedirect(reverse('products:list'))

    is_displaying_form = Pick_display_cl_products(data={
                        'columns': [k for k, v in display_cl.items() if v]})

    products = Products.objects.values()

    if request.GET != {}:
        if 'page' in request.GET.keys():
            page = int(request.GET.get('page'))
            list_only = request.GET.get('list_only')

        if 'reset' in request.GET.keys():
            return HttpResponseRedirect(reverse('products:list'))
        form = Filter_products(data=request.GET)
        if form.is_valid():
            filt = filter_products(request.GET)
            products = products.filter(*filt).output_list(order_cl, display_cl)
    else:
        form = Filter_products()
        products = products.output_list(order_cl, display_cl)

    products_paginator = get_paginator(products, list_only, page)
    if products_paginator is None:
        return HttpResponse('')

    request_get_dict = '?' + '&'.join(f'{k}={v}' for k, v
                                      in request.GET.items() if k != 'page') + '&page='

    context = {
        'title': 'Продукция',
        'products': products_paginator,
        'form_filter': form,
        'columns': columns,
        'display_form': is_displaying_form,
        'request_get': request_get_dict,
        'page_range': products_paginator.paginator.get_elided_page_range(
                                                                page,
                                                                on_each_side=6),
               }

    if list_only:
        return render(request, 'products/table_products.html', context)

    return render(request, 'products/list_products.html', context)


@login_required
def show_product(request: HttpRequest,
                 alcocode: Optional[int] = None) -> HttpResponse:
    if alcocode is None:
        HttpResponseRedirect(reverse('products:list'))

    order_cl, display_cl, columns, _ = get_user_settings(request.user.username,
                                                         'shipments')

    product = get_object_or_404(Products, alcocode=alcocode)
    carts = product.cartproducts_set.all()
    shipments = Shipments.objects.filter(
                id__in=[i['shipment_id'] for i in carts.values()]).exclude(
                    condition__in=['Распроведено', 'Отклонено ЕГАИС']).output_list(
                                                                    order_cl, display_cl)
    form_date = Select_date(data={'date_select': 'month'})

    statistics_per_month = get_sum_cart(carts.filter(
                                shipment_id__in=[i['id'] for i in shipments.ships_per_month()]))
    statistics_per_year = get_sum_cart(carts.filter(
                                    shipment_id__in=[i['id'] for i in shipments.ships_per_year()]))

    statistics_per_month['unique_clients'] = shipments.ships_per_month().get_unique_clients()
    statistics_per_year['unique_clients'] = shipments.ships_per_year().get_unique_clients()
    statistics_per_month['count'] = shipments.ships_per_month().count()
    statistics_per_year['count'] = shipments.ships_per_year().count()

    context = {'title': product.full_name,
               'product': product,
               'form_date': form_date,
               'shipments': shipments[:50],
               'columns': columns,
               'statistics_per_month': statistics_per_month,
               'statistics_per_year': statistics_per_year,
               }
    return render(request, 'products/product.html', context)
