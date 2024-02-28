from users.models import Users, SettingsUsers


COLUMNS_SHIPS = {'id': 'id',
                'num': 'Номер',
                'condition': 'Состояние',
                'uuid': 'UUID',
                'ttn': 'TTN-номер',
                'fix_number': 'FIX-номер',
                'date_creation': 'Дата создания',
                'date_fixation': 'Дата фиксации',
                'client__full_name':'Получатель',
                'client__fsrar_id': 'FSRAR ID получателя',}

COLUMNS_CLIENTS = {'fsrar_id': 'FSRAR ID получателя',
                   'full_name':'Получатель',
                   'inn':'ИНН',
                   'kpp':'КПП',
                   'adress': 'Адрес',}

COLUMNS_PRODUCTS = {'alcocode': 'Код ЕГАИС',
                    'full_name':'Наименование',
                    'capacity': 'Объем',
                    'alcovolume': 'Крепость',
                    'real_alcovolume': 'Факт. крепость',
                    'type_product': 'Тип продукта',
                    'type_code': 'Код вида продукции',
                    'local_reference': 'Собственная',
                    'manufacturer': 'Производитель',}

COLUMNS_MANUFACTURES = {'fsrar_id': 'FSRAR ID получателя',
                        'full_name':'Получатель',}

TABLE_NAME = {'shipments': COLUMNS_SHIPS,
              'clients': COLUMNS_CLIENTS,
              'manufactures': COLUMNS_MANUFACTURES,
              'products': COLUMNS_PRODUCTS,}


def sort_order_cl(cl_dict) -> dict:
    # {name_columns: order}
    return dict(sorted(cl_dict.items(), key=lambda a: a[1]))

def create_default_order_col(table) -> dict:
    # {name_columns: order}
    res = {i:index for index, i in enumerate(
                        table.keys())}
    return res

def create_default_display_col(table) -> dict:
    #{name_columns: is_display}
    res = {i:1 for i in table.keys()}
    return res

def output_cl(cl_list: dict, name_table) -> list:
    cl: list = []
    for name, item in cl_list.items():
        if item:
            cl.append((name_table[name], name))
    return cl

def get_user_settings(username, table):
    user = Users.objects.get(username=username)
    try:
        set_user = SettingsUsers.objects.get(username=user.id)
    except SettingsUsers.DoesNotExist:
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
            #...new list models

        set_user.save()

    if table == 'shipments':
        order_cl: dict = sort_order_cl(set_user.order_col_ship_lst)
        display_cl: dict = set_user.display_col_ship_lst
    elif table == 'clients':
        order_cl: dict = sort_order_cl(set_user.order_col_client_lst)
        display_cl: dict = set_user.display_col_client_lst
    elif table == 'products':
        order_cl: dict = sort_order_cl(set_user.order_col_product_lst)
        display_cl: dict = set_user.display_col_product_lst
    elif table == 'manufacture':
        order_cl: dict = sort_order_cl(set_user.order_col_manufacture_lst)
        display_cl: dict = set_user.display_col_manufacture_lst
    #...new list models

    columns: list = output_cl(display_cl, TABLE_NAME[table])
    columns = sorted(columns, key=lambda a: order_cl[a[1]])
    return order_cl, display_cl, columns, set_user

def change_displaying_cl(request, settings_user, name_list):
    print(request.POST.getlist('columns'), name_list)
    if name_list == 'shipments':
        for key in settings_user.display_col_ship_lst.keys():
            if key in request.POST.getlist('columns') or key == 'id':
                settings_user.display_col_ship_lst[key] = 1
            else: 
                settings_user.display_col_ship_lst[key] = 0

    elif name_list == 'clients':
        for key in settings_user.display_col_client_lst.keys():
            if key in request.POST.getlist('columns') or key == 'fsrar_id':
                settings_user.display_col_client_lst[key] = 1
            else: 
                settings_user.display_col_client_lst[key] = 0

    elif name_list == 'products':

        for key in settings_user.display_col_product_lst.keys():
            if key in request.POST.getlist('columns') or key == 'alcocode':
                settings_user.display_col_product_lst[key] = 1
            else: 
                settings_user.display_col_product_lst[key] = 0
    settings_user.save()
