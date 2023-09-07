from time import sleep
from threading import Thread
from app.logs import logger
from app.shipments import Shipment, parsing_shipments
from app.utm_queue import run_doc_picker
from base.database import Database

active_shipments: dict = {}
acts: dict = {}
db = Database('postgres')

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
    th_queue_utm = Thread(target=run_doc_picker, args=[active_shipments, acts], daemon=True)
    th_parsing_docs = Thread(target=parsing_shipments, args=[active_shipments, acts, db], daemon=True)
    th_queue_utm.start()
    th_parsing_docs.start()
    
    while True:
        try:
            print('Поток очередь утм:', th_queue_utm.is_alive(), ' Поток парсинг документов:', th_parsing_docs.is_alive())
            print(f'Акты: {acts}')
            for i, item in active_shipments.items(): 
                print(f'{i}: {item.number}')
            sleep(30)
        except KeyboardInterrupt:
            db.connection.close()
            exit()
    

if __name__ == '__main__':
    start()
