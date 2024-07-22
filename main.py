import asyncio
import os
from threading import Thread
from time import sleep

from multiprocess import Process

from app.configuration import get_automatic_print, get_start_app
from app.consumer_utm import Consumer_utm_queue
from app.logs import logger
from app.models.shipments import Shipment, parsing_shipments
from app.utm_queue import Aio_utm_queue, run_doc_picker
from base.database import Database

active_shipments: dict = {}
acts: dict = {}
db = Database('postgres')


def get_active_shipments() -> None:
    response = db.select_active_shipments()
    if len(response) == 0:
        return
    for ship in response:
        active_shipments[ship[2]] = Shipment(ship[2], '', ship[1])
        active_shipments[ship[2]].id_in_base = ship[0]
        active_shipments[ship[2]].number = ship[3]
        for product in ship[4]:
            active_shipments[ship[2]].products[product[0]] = {'form2_old': product[1]}


@logger.catch(onerror=lambda _: db.connection.close())
def legacy_start() -> None:
    get_active_shipments()
    th_queue_utm = Thread(target=run_doc_picker,
                          args=[active_shipments, acts],
                          daemon=True)
    th_parsing_docs = Thread(target=parsing_shipments,
                             args=[active_shipments, acts, db],
                             daemon=True)
    th_queue_utm.start()
    db.update_status_modules('utm_queue', True)
    th_parsing_docs.start()
    db.update_status_modules('parsing_shipments', True)

    check_pars, check_queue = 0, 0
    while True:
        try:
            print('Поток очередь утм:', th_queue_utm.is_alive(),
                  ' Поток парсинг документов:', th_parsing_docs.is_alive())

            if th_queue_utm.is_alive() is False and check_queue == 0:
                db.update_status_modules('queue_utm', False)
                check_queue = 1
            if th_parsing_docs.is_alive() is False and check_pars == 0:
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


def start_process_tracking_utm() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    aio = Aio_utm_queue('ex-utm')
    loop.run_until_complete(aio.run_doc_picker())


def start_process_parsing_shipments() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    consumer = Consumer_utm_queue('ex-utm')
    loop.run_until_complete(consumer.start())


def start_process_celery_eventlet():
    path_file = os.path.realpath(__file__)
    dir_path = os.path.dirname(path_file)
    os.system(f'cd {dir_path}/urme && celery -A urme worker -l INFO -P eventlet')


@logger.catch(onerror=lambda _: db.connection.close())
def start() -> None:
    pr_queue_utm = Process(target=start_process_tracking_utm, daemon=True)
    pr_parsing_docs = Process(target=start_process_parsing_shipments, daemon=True)
    pr_auto_print = Process(target=start_process_celery_eventlet, daemon=True)

    pr_queue_utm.start()
    db.update_status_modules('utm_queue', True)
    pr_parsing_docs.start()
    db.update_status_modules('parsing_shipments', True)

    if get_automatic_print():
        pr_auto_print.start()

    check_pars, check_queue = 0, 0
    while True:
        try:
            print('Процесс - очередь утм:', pr_queue_utm.is_alive(),
                  '| Процесс - парсинг документов:', pr_parsing_docs.is_alive())

            if pr_queue_utm.is_alive() == 0 and check_queue == 0:
                db.update_status_modules('queue_utm', False)
                check_queue = 1
            if pr_parsing_docs.is_alive() == 0 and check_pars == 0:
                db.update_status_modules('parsing_shipments', False)
                check_pars = 1
            sleep(60)
        except KeyboardInterrupt:
            db.update_status_modules('utm_queue', False)
            db.update_status_modules('parsing_shipments', False)
            db.connection.close()
            pr_queue_utm.join()
            pr_parsing_docs.join()
            exit()


if __name__ == '__main__':
    if get_start_app():
        legacy_start()
    else:
        start()
