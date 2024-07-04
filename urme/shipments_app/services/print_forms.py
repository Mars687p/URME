import os
import subprocess
from typing import Optional

import win32api
import win32print
from products.services import get_sum_cart
from shipments_app.models import Shipments
from users.models import DetailsOrganization

from app.logs import logger
from urme.settings import path_chrome


def html_to_pdf(html: str) -> str:
    command = f'{path_chrome} --headless --disable-gpu --print-to-pdf="{html}.pdf" "{html}.html"'
    subprocess.Popen(command).wait()
    return f'{html}.pdf'


def print_pdf(input_pdf: str,
              name_print: Optional[str] = None) -> None:
    if name_print is None:
        name_print = win32print.GetDefaultPrinter()

    # тут нужные права на использование принтеров
    printdefaults = {"DesiredAccess": win32print.PRINTER_ALL_ACCESS}
    # начинаем работу с принтером ("открываем" его)
    handle = win32print.OpenPrinter(name_print, printdefaults)
    # Если изменить level на другое число, то не сработает
    level = 2
    # Получаем значения принтера
    attributes = win32print.GetPrinter(handle, level)
    # Передаем нужные значения в принтер
    win32print.SetPrinter(handle, level, attributes, 0)
    # Предупреждаем принтер о старте печати
    win32print.StartDocPrinter(handle, 1, [input_pdf, None, "raw"])

    # (Открытие окна, что сделать, путь к файлу, параметры запуска,
    # путь к директории, что сделать после)
    win32api.ShellExecute(0, 'print', input_pdf, '.', '.', 0)
    win32print.ClosePrinter(handle)


def clear_dir_pdf(path_dir: str) -> None:
    for filename in os.listdir(path_dir):
        file_path = os.path.join(path_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f'Ошибка при удалении файла {file_path}. {e}')


def get_context_for_printform(ship_id: int) -> dict:
    shipment = Shipments.objects.select_related('client').get(id=ship_id)
    transport = shipment.transports_set.first().get_values_form()
    cart_products = shipment.cartproducts_set.all()
    org = DetailsOrganization.objects.get(fsrar_id=10000000444)
    sum_cart = get_sum_cart(cart_products)

    context = {
            'title': f'Накладная {shipment.num}',
            'tr': transport,
            'cart': cart_products,
            'org': org,
            'sum_cart': sum_cart,
            'shipment': shipment}
    return context
