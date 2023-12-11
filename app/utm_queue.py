import json
import requests
from time import sleep
from threading import RLock

from app.configuration import get_url_utm
from app.shipments import Shipment
from app.logs import logger


base_url: str = get_url_utm()

class Queue_utm:
    def __init__(self) -> None:
        pass

    def get_outgoing_docs(self, active_shipments):
        #collect all shipments 
        response_out_docs = json.loads(requests.get(base_url + 'api/db/in/list?offset=0&limit=20').text)
        
        for row in response_out_docs['rows']:
            if row['docType'] == 'WayBill_v4':
                if row['uuid'] not in active_shipments.keys():
                    active_shipments[row['uuid']] = Shipment(row['uuid'], requests.get(base_url + f'api/db/in/{row["id"]}').text)

    def get_incoming_docs(self, active_shipments, acts):
        #Pick up all the files associated with the shipment by uuid
        response_in_docs = json.loads(requests.get(base_url + 'api/db/out/list?offset=0&limit=20').text)
        for row in response_in_docs['rows']:
            if row['docType'] == 'WayBillAct_v4':
                if row['id'] not in acts.keys():
                    acts[row['id']] = requests.get(base_url + f'api/db/out/{row["id"]}').text

            if row['replyId'] in active_shipments.keys():
                if row['id'] not in active_shipments[row['replyId']].incomings_xml.keys():
                    active_shipments[row['replyId']].incomings_xml[row['id']] = [row['docType'], requests.get(base_url + f'api/db/out/{row["id"]}').text]

@logger.catch
def run_doc_picker(docs, acts):
    queue = Queue_utm()
    locks = RLock()
    is_err = False
    while True:
        locks.acquire()
        try:
            queue.get_outgoing_docs(docs)
            queue.get_incoming_docs(docs, acts)
            if is_err:
                is_err = False
                logger.info('utm_queue: Подключение к УТМ восстановлено.')
        except (TimeoutError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, OSError) as err:
            if is_err == False:
                logger.error(f'Ошибка в потоке парсинга(нет подключения к УТМ): {err}')
                is_err = True
        locks.release()
        sleep(2)