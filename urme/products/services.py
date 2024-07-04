from decimal import Decimal
from typing import Callable, Optional, TypedDict

from django.db.models import Q, QuerySet, Sum
from django.http import QueryDict
from django.shortcuts import get_object_or_404

from .models import Products


class FilterName(TypedDict):
    alcocode: Callable
    full_name: Callable
    capacity: Callable
    alcovolume: Callable
    type_product: Callable
    type_code: Callable
    is_own: Callable


class SumCart(TypedDict):
    quantity: int
    volume: Decimal
    price: Decimal
    volume_abs: Decimal


def get_products(alcocode: Optional[int]) -> QuerySet | Products:
    if alcocode is None:
        return Products.objects.all()
    else:
        return get_object_or_404(Products, alcocode=alcocode)


def get_sum_cart(cart: QuerySet) -> SumCart:
    return SumCart({
            'quantity': [0 if cart.aggregate(Sum('quantity'))['quantity__sum'] is None
                         else cart.aggregate(Sum('quantity'))['quantity__sum']][0],
            'volume': round(sum(item.get_volume_dal() for item in cart), 2),
            'price': sum(item.get_price_position() for item in cart),
            'volume_abs': sum(item.get_abs_volume() for item in cart)})


def filter_products(request_get: QueryDict) -> list[Q]:
    filters: list[Q] = []
    if request_get == {}:
        return filters

    for filter_name in request_get:
        if len(request_get[filter_name]) < 0:
            continue
        try:
            filters += NAME_FILTER[filter_name](request_get, filter_name)  # type: ignore
        except KeyError:
            break

    return filters


def _get_capacity_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    capacity_value = request_get.getlist(filter_name)
    filters: list[Q] = []
    if 'None' in capacity_value:
        capacity_value.remove('None')
        filters.append(Q(capacity__in=capacity_value) | Q(capacity__isnull=True))
    else:
        filters.append(Q(capacity__in=capacity_value))
    return filters


def _get_alcocode_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    fsrar_id = request_get[filter_name]
    filters.append(Q(alcocode__icontains=fsrar_id))
    return filters


def _get_full_name_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    filters.append(Q(full_name__icontains=request_get[filter_name]))
    return filters


def _get_alcovolume_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    filters.append(Q(alcovolume__in=request_get.getlist(filter_name)))
    return filters


def _get_type_product_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    filters.append(Q(type_product__in=request_get.getlist(filter_name)))
    return filters


def _get_type_code_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    filters.append(Q(type_code__in=request_get.getlist(filter_name)))
    return filters


def _get_isown_filter(request_get: QueryDict, filter_name: str) -> list[Q]:
    filters: list[Q] = []
    if request_get.get(filter_name) == 'on':
        filters.append(Q(local_reference=True))
    return filters


NAME_FILTER = FilterName({
    'alcocode': _get_alcocode_filter,
    'alcovolume': _get_alcovolume_filter,
    'capacity': _get_capacity_filter,
    'full_name': _get_full_name_filter,
    'is_own': _get_isown_filter,
    'type_code': _get_type_code_filter,
    'type_product': _get_type_product_filter
})
