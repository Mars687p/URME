
from enum import Enum

from django.db.models import Q
from django.http import QueryDict
from django.utils import timezone


class FilterValue(Enum):
    date_start = ''
    date_pick = ''


class FilterDatePick(Enum):
    TODAY = 'today'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'


def filters_ships(request_get: QueryDict) -> list[Q]:
    filters: list[Q] = []

    for name_filter in request_get:
        if len(request_get[name_filter]) < 0 or request_get[name_filter] == '':
            continue

        if name_filter == 'date_start':
            filters += _get_date_start_filter(request_get[name_filter])

        elif name_filter == 'date_pick' and len(request_get['date_start']) == 0:
            filters += _get_date_pick_filter(request_get['date_pick'])

        elif name_filter == 'number':
            nums = request_get[name_filter]
            filters += _get_number_filter(nums)

        elif name_filter == 'client':
            client = request_get[name_filter]
            filters += _get_client_filter(client)

        elif name_filter == 'sel-con':
            condition = request_get[name_filter]
            filters += _get_condition_filter(condition)
    return filters


def _get_date_pick_filter(date_pick: str) -> list[Q]:
    date = timezone.now()
    filters: list[Q] = []
    match date_pick:
        case FilterDatePick.TODAY.value:
            filters.append(Q(date_creation=date))
        case FilterDatePick.WEEK.value:
            filters.append(Q(date_creation__week=date.isocalendar().week))
            filters.append(Q(date_creation__year=date.year))
        case FilterDatePick.MONTH.value:
            filters.append(Q(date_creation__month=date.month))
            filters.append(Q(date_creation__year=date.year))
        case FilterDatePick.YEAR.value:
            filters.append(Q(date_creation__year=date.year))
        case _:
            raise AttributeError
    return filters


def _get_number_filter(num_variable: str) -> list[Q]:
    """
    If the number is written with a hyphen, then it is a range
    If the numbers are written with spaces, then these are numbers
    Otherwise it's one number
    """
    filters: list[Q] = []
    range_num = num_variable.split('-')
    # check range
    if len(range_num) == 2:
        range_num = sorted(range_num)
        filters.append(Q(num__range=range_num))
    # check number by a space
    else:
        range_num = num_variable.split()
        if len(range_num) > 1:
            filters.append(Q(num__in=range_num))
        # one number
        else:
            filters.append(Q(num__contains=num_variable))
    return filters


def _get_client_filter(client: str) -> list[Q]:
    filters: list[Q] = []
    try:
        fsrar_id = int(client)
        filters.append(Q(client__fsrar_id__icontains=fsrar_id))
    except ValueError:
        filters.append(Q(client__full_name__icontains=client))
    return filters


def _get_condition_filter(condition: str) -> list[Q]:
    filters: list[Q] = []
    if condition[0] != '0':
        filters.append(Q(condition=condition))
    return filters


def _get_date_start_filter(date_start: str) -> list[Q]:
    filters: list[Q] = []
    if date_start != '':
        filters.append(Q(date_creation=date_start))
    return filters
