import win32print, win32api
import subprocess, os

from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage

from shipments_app.models import Shipments
from products.utils import get_sum_cart
from users.models import DetailsOrganization
from urme.settings import path_chrome

from app.logs import logger

def filters_ships(request_get) -> list:
    date = timezone.now()
    filters = []
    if request_get != {}:
        for filter in request_get:
            if len(request_get[filter]) > 0:
                if filter == 'date_start':
                    filters.append(Q(date_creation=request_get[filter]))       
                if filter == 'date_pick' and len(request_get['date_start']) == 0:
                    if 'today' in request_get['date_pick']:
                        filters.append(Q(date_creation=date))
                    if 'week' in request_get['date_pick']:
                        filters.append(Q(date_creation__week=date.isocalendar().week))
                    if 'month' in request_get['date_pick']:
                        filters.append(Q(date_creation__month=date.month))
                    if 'year' in request_get['date_pick']:
                        filters.append(Q(date_creation__year=date.year))
                if filter == 'number':
                    range_num = request_get[filter].split('-')
                    #check range
                    if len(range_num) == 2:
                        filters.append(Q(num__range=range_num))
                    # check number by a space
                    if len(range_num) == 1:
                        range_num =request_get[filter].split()
                        if len(range_num) > 1:
                            filters.append(Q(num__in=range_num))
                        # one number
                        else: 
                            filters.append(Q(num__contains=request_get[filter]))
                if filter == 'client':
                    try:
                        fsrar_id = int(request_get[filter])
                        filters.append(Q(client__fsrar_id__icontains=fsrar_id))
                    except ValueError:
                        filters.append(Q(client__full_name__icontains=request_get[filter]))
                #condition filter
                if filter == 'sel-con':
                    if request_get[filter][0] != '0':
                        filters.append(Q(condition__icontains=request_get[filter]))
        return filters

def get_paginator(queryset, list_only, page):
    per_page = 50
    paginator = Paginator(queryset, per_page)
    try:
        queryset_paginator = paginator.page(page)
    except EmptyPage:
        if list_only: 
            return None
        queryset_paginator = paginator.page(paginator.num_pages)
    return queryset_paginator


def get_context_for_printform(ship_id) -> dict:
    shipment = Shipments.objects.select_related('client').get(id=ship_id)
    transport = shipment.transports_set.first().get_values_form()
    cart_products = shipment.cartproducts_set.all()
    org = DetailsOrganization.objects.get(fsrar_id=10000000444)
    sum_cart = get_sum_cart(cart_products)

    context = {'title': f'Накладная {shipment.num}',
            'tr': transport,
            'cart': cart_products,
            'org': org,
            'sum_cart': sum_cart,
            'shipment': shipment}      
    return context


def html_to_pdf(html):
    command = f'{path_chrome} --headless --disable-gpu --print-to-pdf="{html}.pdf" "{html}.html"'
    subprocess.Popen(command).wait()
    return f'{html}.pdf'


def print_pdf(input_pdf, name_print=None) -> None:
    if name_print == None:
        name_print = win32print.GetDefaultPrinter()

    ## тут нужные права на использование принтеров
    printdefaults = {"DesiredAccess": win32print.PRINTER_ALL_ACCESS}
    ## начинаем работу с принтером ("открываем" его)
    handle = win32print.OpenPrinter(name_print, printdefaults)
    ## Если изменить level на другое число, то не сработает
    level = 2
    ## Получаем значения принтера
    attributes = win32print.GetPrinter(handle, level)
    # Передаем нужные значения в принтер
    win32print.SetPrinter(handle, level, attributes, 0)
    # Предупреждаем принтер о старте печати
    win32print.StartDocPrinter(handle, 1, [input_pdf, None, "raw"])

    # (Открытие окна, что сделать, путь к файлу, параметры запуска, путь к директории, что сделать после)
    win32api.ShellExecute(0, 'print', input_pdf, '.', '.', 0)
    win32print.ClosePrinter(handle)

def clear_dir_pdf(path_dir):
    for filename in os.listdir(path_dir):
        file_path = os.path.join(path_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f'Ошибка при удалении файла {file_path}. {e}')


    
                

                



