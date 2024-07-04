from typing import Dict

from django.http import HttpRequest
from users.models import SettingsUsers, Users

COLUMNS_SHIPS = {
                'id': 'id',
                'num': 'Номер',
                'condition': 'Состояние',
                'uuid': 'UUID',
                'ttn': 'TTN-номер',
                'fix_number': 'FIX-номер',
                'date_creation': 'Дата создания',
                'date_fixation': 'Дата фиксации',
                'client__full_name': 'Получатель',
                'client__fsrar_id': 'FSRAR ID получателя'}

COLUMNS_CLIENTS = {'fsrar_id': 'FSRAR ID получателя',
                   'full_name': 'Получатель',
                   'inn': 'ИНН',
                   'kpp': 'КПП',
                   'adress': 'Адрес'}

COLUMNS_PRODUCTS = {'alcocode': 'Код ЕГАИС',
                    'full_name': 'Наименование',
                    'capacity': 'Объем',
                    'alcovolume': 'Крепость',
                    'real_alcovolume': 'Факт. крепость',
                    'type_product': 'Тип продукта',
                    'type_code': 'Код вида продукции',
                    'local_reference': 'Собственная',
                    'manufacturer': 'Производитель'}

COLUMNS_MANUFACTURES = {'fsrar_id': 'FSRAR ID получателя',
                        'full_name': 'Получатель'}

TABLE_NAME = {
            'shipments': COLUMNS_SHIPS,
            'clients': COLUMNS_CLIENTS,
            'manufactures': COLUMNS_MANUFACTURES,
            'products': COLUMNS_PRODUCTS}


def sort_order_cl(cl_dict: Dict[str, int]) -> Dict[str, int]:
    # {name_columns: order}
    return dict(sorted(cl_dict.items(), key=lambda a: a[1]))


def create_default_order_col(table: dict) -> Dict[str, int]:
    # {name_columns: order}
    res = {i: index for index, i in enumerate(
                        table.keys())}
    return res


def create_default_display_col(table: Dict[str, str]) -> dict:
    # {name_columns: is_display}
    res = {i: 1 for i in table.keys()}
    return res


def output_cl(cl_list: dict, dict_table: Dict[str, str]) -> list:
    cl: list = []
    for name, item in cl_list.items():
        if item:
            cl.append((dict_table[name], name))
    return cl


def get_user_settings(username: str, table: str) -> tuple:
    user = Users.objects.get(username=username)
    try:
        set_user = SettingsUsers.objects.get(username=user.id)
    except SettingsUsers.DoesNotExist:
        _create_default_user_settings(user)

    if table == 'shipments':
        order_cl = sort_order_cl(set_user.order_col_ship_lst)
        display_cl = set_user.display_col_ship_lst
    elif table == 'clients':
        order_cl = sort_order_cl(set_user.order_col_client_lst)
        display_cl = set_user.display_col_client_lst
    elif table == 'products':
        order_cl = sort_order_cl(set_user.order_col_product_lst)
        display_cl = set_user.display_col_product_lst
    elif table == 'manufacture':
        order_cl = sort_order_cl(set_user.order_col_manufacture_lst)
        display_cl = set_user.display_col_manufacture_lst
    # ...new list models

    columns: list = output_cl(display_cl, TABLE_NAME[table])
    columns = sorted(columns, key=lambda a: order_cl[a[1]])
    return order_cl, display_cl, columns, set_user


def change_displaying_cl(request: HttpRequest,
                         settings_user: SettingsUsers,
                         name_list: str) -> None:
    if name_list == 'shipments':
        _change_display_cl_ships(settings_user, request)
    elif name_list == 'clients':
        _change_display_cl_clients(settings_user, request)
    elif name_list == 'products':
        _change_display_cl_products(settings_user, request)
    settings_user.save()


def user_change_order_cl(request: HttpRequest) -> bool:
    table_name = request.POST['table_name'].replace('/', '')
    user = SettingsUsers.objects.get(username=request.user.id)
    order_cl = {k: int(i)+1 for k, i in request.POST.items() if k != 'table_name'}
    if table_name == 'shipments':
        order_cl['id'] = 0
        user.order_col_ship_lst = order_cl
    elif table_name == 'clients':
        order_cl['fsrar_id'] = 0
        user.order_col_client_lst = order_cl
    elif table_name == 'products':
        order_cl['alcocode'] = 0
        user.order_col_product_lst = order_cl
    user.save()
    return True


def _create_default_user_settings(user: Users) -> None:
    set_user = SettingsUsers()
    set_user.username = user
    for key in TABLE_NAME.keys():
        if key == 'shipments':
            set_user.order_col_ship_lst = create_default_order_col(TABLE_NAME[key])
            set_user.display_col_ship_lst = create_default_display_col(TABLE_NAME[key])
        elif key == 'clients':
            set_user.order_col_client_lst = create_default_order_col(TABLE_NAME[key])
            set_user.display_col_client_lst = create_default_display_col(TABLE_NAME[key])
        elif key == 'products':
            set_user.order_col_product_lst = create_default_order_col(TABLE_NAME[key])
            set_user.display_col_product_lst = create_default_display_col(TABLE_NAME[key])
        elif key == 'manufactures':
            set_user.order_col_manufacture_lst = create_default_order_col(TABLE_NAME[key])
            set_user.display_col_manufacture_lst = create_default_display_col(TABLE_NAME[key])
        # ...new list models

    set_user.save()


def _change_display_cl_ships(settings_user: SettingsUsers,
                             request: HttpRequest) -> None:
    for key in settings_user.display_col_ship_lst.keys():
        if key in request.POST.getlist('columns') or key == 'id':
            settings_user.display_col_ship_lst[key] = 1
        else:
            settings_user.display_col_ship_lst[key] = 0


def _change_display_cl_clients(settings_user: SettingsUsers,
                               request: HttpRequest) -> None:
    for key in settings_user.display_col_client_lst.keys():
        if key in request.POST.getlist('columns') or key == 'fsrar_id':
            settings_user.display_col_client_lst[key] = 1
        else:
            settings_user.display_col_client_lst[key] = 0


def _change_display_cl_products(settings_user: SettingsUsers,
                                request: HttpRequest) -> None:
    for key in settings_user.display_col_product_lst.keys():
        if key in request.POST.getlist('columns') or key == 'alcocode':
            settings_user.display_col_product_lst[key] = 1
        else:
            settings_user.display_col_product_lst[key] = 0
