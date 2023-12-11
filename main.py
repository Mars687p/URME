from time import sleep
from threading import Thread
from app.logs import logger
from app.shipments import Shipment, parsing_shipments
from app.utm_queue import run_doc_picker
from base.database import Database

active_shipments: dict = {}
acts: dict = {}
db = Database('postgres')
#FOR DEL db_for_TEST
db_for_test = Database('dj_user', 'test2')


def get_active_shipments() -> None:
    response = db.select_active_shipments()
    if len(response) == 0: return
    for ship in response:
        active_shipments[ship[2]] = Shipment(ship[2], '', ship[1])
        active_shipments[ship[2]].id_in_base = ship[0]
        active_shipments[ship[2]].number = ship[3]
        for product in ship[4]:
            active_shipments[ship[2]].products[product[0]] = {'form2_old': product[1]}



@logger.catch(onerror=lambda _: db.connection.close())
def start() -> None:
    get_active_shipments()
    #FOR DEL db_for_TEST
    th_queue_utm = Thread(target=run_doc_picker, args=[active_shipments, acts], daemon=True)
    th_parsing_docs = Thread(target=parsing_shipments, args=[active_shipments, acts, db, db_for_test], daemon=True)
    th_queue_utm.start()
    db.update_status_modules('utm_queue', True)
    th_parsing_docs.start()
    db.update_status_modules('parsing_shipments', True)
    
    check_pars, check_queue = 0, 0
    while True:
        try:
            print('Поток очередь утм:', th_queue_utm.is_alive(), ' Поток парсинг документов:', th_parsing_docs.is_alive())
            
            if th_queue_utm.is_alive() == False and check_queue == 0:
                db.update_status_modules('queue_utm', False)
                check_queue = 1
            if th_parsing_docs.is_alive() == False and check_pars == 0:
                db.update_status_modules('parsing_shipments', False)
                check_pars = 1

            for i, item in active_shipments.items(): 
                print(f'{i}: {item.number}')
            sleep(30)
        except KeyboardInterrupt:
            db.update_status_modules('utm_queue', False)
            db.update_status_modules('parsing_shipments', False)
            db.connection.close()
            exit()
    

if __name__ == '__main__':
    start()
