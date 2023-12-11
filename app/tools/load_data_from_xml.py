import easygui
from app.shipments import Shipment, parsing_acts
from app.logs import logger
from base.database import Database


FILE_TYPES = ['Отгрузка', 'Акт']

def get_paths_files() -> list:
    return easygui.fileopenbox(default='C:/progs/Autoshipment/failed_parse/*.xml', filetypes=['*.xml'], multiple=True)

def get_type_file():
    return easygui.buttonbox('Выберите тип файла', choices=FILE_TYPES)
    

def write_files(paths) -> list:
    files = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            files.append(f.read())
    return files
            

def create_shipment(files) -> list:
    ships = []
    for file in files:
        ships.append(Shipment('repeat', file, 'Принято ЕГАИС'))
    for ship in ships:
        ship.parsing_outgoing_doc()
    return ships

def create_act(files):
    acts = []
    for file in files:
        acts.append(parsing_acts(file))
    return acts

def write_in_db(data, tf) -> None:
    if tf == FILE_TYPES[0]:
        for ship in data:
            sql = """SELECT id, num, date_creation, uuid FROM shipments
                    where date_creation = %s and num = %s"""
            response = db.select_sql(sql, (ship.date, ship.number))
            if response == None: 
                db.insert_record_shipment(ship)
            else:
                ship.id_in_base = response[0]
                db.update_record_shipment(ship)
    if tf == FILE_TYPES[1]:
        for act in data:
            db.update_record_waybill_act(*act)

def start():
    paths_files = get_paths_files()
    files = write_files(paths_files)
    tf = get_type_file()
    if tf == FILE_TYPES[0]:
        data = create_shipment(files)
    if tf == FILE_TYPES[1]:
        data = create_act(files)
    try:
        write_in_db(data, tf)
    except Exception as err:
        logger.info(err)
    db.connection.close()

if __name__ == '__main__':
    db = Database('postgres')
    start()