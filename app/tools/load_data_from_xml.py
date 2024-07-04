from typing import Literal, Union

import easygui

from app.logs import logger
from app.models.shipments import Shipment, parsing_acts
from base.database import Database
from exeptions.parsing_error import ParsingError

FILE_TYPES = ('Отгрузка', 'Акт')


def get_paths_files() -> list[str]:
    return easygui.fileopenbox(default='C:/progs/Autoshipment/failed_parse/*.xml',
                               filetypes=['*.xml'],
                               multiple=True)


def get_type_file() -> tuple[Literal['Отгрузка'], Literal['Акт']]:
    return easygui.buttonbox('Выберите тип файла', choices=FILE_TYPES)


def read_files(paths: list[str]) -> list[str]:
    files = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            files.append(f.read())
    return files


def create_shipment(files: list[str]) -> list[Shipment]:
    ships: list[Shipment] = []
    for file in files:
        ships.append(Shipment('repeat', file, None, 'Принято ЕГАИС'))  # type: ignore
    for ship in ships:
        try:
            ship.parsing_outgoing_doc_v4()
            ship._load_from_file()
        except ParsingError as _ex:
            logger.error(_ex)
            exit()
    return ships


def create_act(files: list) -> list:
    acts = []
    for file in files:
        acts.append(parsing_acts(file))
    return acts


def write_ships(lst_files: list[Shipment]) -> None:
    for ship in lst_files:
        sql = """SELECT id, num, date_creation, uuid FROM shipments
                where date_creation = %s and num = %s"""
        response = db.select_sql(sql, (ship.date, ship.number))
        if response is None:
            ship_id = db.insert_record_shipment(ship)
            ship.id_in_base = ship_id
        else:
            ship.id_in_base = response[0]

        db.update_record_shipment(ship)


def write_in_db(lst_files: list[Union[Shipment, list]],
                tf: tuple[Literal['Отгрузка'], Literal['Акт']]) -> None:
    if tf == FILE_TYPES[0]:
        write_ships(lst_files)  # type: ignore
    if tf == FILE_TYPES[1]:
        for act in lst_files:
            db.update_record_waybill_act(*act)


def start() -> None:
    paths_files = get_paths_files()
    files = read_files(paths_files)
    tf = get_type_file()
    if tf == FILE_TYPES[0]:
        lst_files = create_shipment(files)
    if tf == FILE_TYPES[1]:
        lst_files = create_act(files)
    try:
        write_in_db(lst_files, tf)  # type: ignore
    except Exception as err:
        logger.info(err)
    db.connection.close()


if __name__ == '__main__':
    db = Database('postgres')
    start()
