import asyncio
import json
from threading import RLock
from time import sleep
from typing import Any, Dict, NoReturn, no_type_check

import aiohttp
import aiohttp.client_exceptions
import requests
from aio_pika.abc import AbstractIncomingMessage
from aiormq.exceptions import AMQPConnectionError

from app.handlers.docs_manufactures import HandlerMFDocs
from app.handlers.docs_shipments import HandlerShipmentsDocs
from app.logs import logger
from app.models.manufactures import Manufacture
from app.models.shipments import Shipment
from app.rabbit import Rabbit
from app.settings import (PAUSE_BEFORE_DEL_SECCONDS, TYPE_ACTS,
                          TYPE_PRODUCT_ACTS, base_url)
from base.database import Async_database
from custom_types.rabbit import RabbitMessageQueueUTM


class Aio_utm_queue:
    def __init__(self, ex_name: str) -> None:
        self.rbmq = Rabbit(ex_name)
        self.db = Async_database('postgres')
        self.session = aiohttp.ClientSession()
        self.active_shipments: Dict[str, Shipment] = {}
        self.active_manufactures: Dict[str, Manufacture] = {}
        self.acts: Dict[int, int] = {}

    async def _get_doc_shipments(self, row: Dict[str, Any]) -> None:
        if row['id'] in self.active_shipments[row['replyId']].incomings_xml.keys():
            return None
        try:
            self.active_shipments[row['replyId']].incomings_xml[row['id']] = []
        except KeyError:
            logger.warning('Keyerror in _get_doc_shipments, aio_utm')
            return None

        await self.get_xml_doc(
                            row['id'],
                            row['replyId'],
                            'shipments',
                            0,
                            row['docType'])

    async def _get_doc_manufactures(self, row: Dict[str, Any]) -> None:
        if row['id'] in \
                self.active_manufactures[row['replyId']].incomings_xml.keys():
            return None
        try:
            self.active_manufactures[row['replyId']].incomings_xml[row['id']] = []
        except KeyError:
            logger.warning('Keyerror in _get_doc_manufactures, aio_utm')
            return None
        await self.get_xml_doc(
                            row['id'],
                            row['replyId'],
                            'manufactures',
                            0,
                            row['docType'])

    async def _get_waybill_act_v4(self, row: Dict[str, Any]) -> None:
        if row['id'] in self.acts.keys():
            return None
        await self.get_xml_doc(
                        row['id'],
                        row['replyId'],
                        'shipments',
                        0,
                        row['docType'])
        self.acts[row['id']] = 0

    async def _get_rej_manufacture(self, row: Dict[str, Any]) -> None:
        if row['id'] not in self.acts.keys():
            await self.get_xml_doc(row['id'],
                                   row['replyId'],
                                   'manufactures',
                                   0,
                                   row['docType'])
            self.acts[row['id']] = 0

    async def _get_reply_form1_manufacture(self, row: Dict[str, Any]) -> None:
        if row['id'] not in self.acts.keys():
            await self.get_xml_doc(
                                row['id'],
                                row['replyId'],
                                'manufactures',
                                0,
                                row['docType'])
            self.acts[row['id']] = 0

    async def _get_act_product(self, row: Dict[str, Any]) -> None:
        if row['id'] not in self.acts.keys():
            await self.get_xml_doc(
                            row['id'],
                            row['replyId'],
                            'product_ref',
                            0,
                            row['docType'])
            self.acts[row['id']] = 0

    @logger.catch
    async def parsing_in_queue(self, row: Dict[str, Any]) -> None:
        if row['replyId'] in self.active_shipments.keys():
            await self._get_doc_shipments(row)

        elif row['replyId'] in self.active_manufactures.keys():
            await self._get_doc_manufactures(row)

        elif row['docType'] == 'WayBillAct_v4':
            await self._get_waybill_act_v4(row)

        elif row['docType'] == 'QueryRejectRepProduced':
            await self._get_rej_manufacture(row)
        elif row['docType'] == 'ReplyForm1':
            await self._get_reply_form1_manufacture(row)

        elif row['docType'] in TYPE_PRODUCT_ACTS:
            await self._get_act_product(row)

    @logger.catch
    async def get_xml_doc(self,
                          id_doc: int,
                          uuid: str,
                          type_doc: str,
                          queue_type: int,
                          type_file: str) -> None:
        # queue_type = 1 - outgoing | 0 - incoming
        if queue_type:
            async with self.session.get(base_url + f'api/db/in/{id_doc}') as resp:
                doc = await resp.text()
                await self.rbmq.publication_task_json(
                                            RabbitMessageQueueUTM({
                                                "type_doc": type_doc,
                                                "uuid": uuid,
                                                "id_doc": id_doc,
                                                "type_file": type_file,
                                                "xml": doc}),
                                            "outgoing-queue")
        else:
            async with self.session.get(base_url + f'api/db/out/{id_doc}') as resp:
                doc = await resp.text()
                await self.rbmq.publication_task_json(
                                            RabbitMessageQueueUTM({
                                                "type_doc": type_doc,
                                                "uuid": uuid,
                                                "id_doc": id_doc,
                                                "type_file": type_file,
                                                "xml": doc}),
                                            "incoming-queue")

    async def get_outgoing_docs(self) -> None:
        async with self.session.get(base_url + 'api/db/in/list?offset=0&limit=10') as resp:
            queue_out = json.loads(await resp.text())
            for row in queue_out['rows']:
                if row['docType'] == 'WayBill_v4':
                    if row['uuid'] not in self.active_shipments.keys():
                        await self.get_xml_doc(
                                                row['id'],
                                                row['uuid'],
                                                'shipments',
                                                1,
                                                row['docType'])
                        self.active_shipments[row['uuid']] = Shipment(row['uuid'],
                                                                      '',
                                                                      self.db)

                if row['docType'] == 'RepProducedProduct_v5':
                    if row['uuid'] not in self.active_manufactures.keys():
                        await self.get_xml_doc(row['id'],
                                               row['uuid'],
                                               'manufactures',
                                               1,
                                               'm_v5')
                        self.active_manufactures[row['uuid']] = Manufacture(row['uuid'],
                                                                            '',
                                                                            self.db)
                if row['docType'] == 'RepProducedProduct_v6':
                    if row['uuid'] not in self.active_manufactures.keys():
                        await self.get_xml_doc(row['id'],
                                               row['uuid'],
                                               'manufactures',
                                               1,
                                               'm_v6')
                        self.active_manufactures[row['uuid']] = Manufacture(row['uuid'],
                                                                            '',
                                                                            self.db)

    async def get_incoming_docs(self) -> None:
        # Pick up all the files associated with the shipment by uuid
        async with self.session.get(base_url +
                                    'api/db/out/list?offset=0&limit=15') as resp_queue:
            queue_in = json.loads(await resp_queue.text())
            await asyncio.gather(*[self.parsing_in_queue(row) for row in queue_in['rows']])

    @logger.catch
    async def clear_active_queue(self, message: AbstractIncomingMessage) -> None:
        msg: RabbitMessageQueueUTM = json.loads(message.body.decode())
        print('CLEAR:', 'mf - ', len(self.active_manufactures),
              '| ships - ', len(self.active_shipments),
              '| acts - ', self.acts)
        async with message.process(ignore_processed=True):
            await message.ack()
        try:
            if msg.get('type_file') == 'FORM2REGINFO':
                del self.active_shipments[msg['uuid']]
            elif msg.get('type_file') == 'FORM1REGINFO':
                del self.active_manufactures[msg['uuid']]
            elif msg.get('type_file') in TYPE_ACTS or \
                    msg.get('type_file') in TYPE_PRODUCT_ACTS:
                await asyncio.sleep(PAUSE_BEFORE_DEL_SECCONDS)
                del self.acts[msg['id_doc']]
            else:
                # for unknown files, del before release
                await asyncio.sleep(PAUSE_BEFORE_DEL_SECCONDS)
                del self.acts[msg['id_doc']]
        except KeyError:
            logger.warning(f"keyerror in clear: {msg}")

    async def xml_from_file(self) -> Dict[str, str]:
        # TODO: сделать обработкой из джанго с загрузкой
        with open(r'E:\progs\Autoshipments\failed_parse\debug.xml',
                  'r',
                  encoding='utf-8') as f:
            file = f.read()
        return {"xml": file,
                "type_doc": "shipments",
                "uuid": "0d5d7c23-82af-4a9b-b836-88d07ad7911a",
                "id_doc": "1",
                "type_file": "FORM2REGINFO"}

    @logger.catch
    async def run_doc_picker(self) -> NoReturn:
        await self.db.get_connection()
        await self.rbmq.start()
        await self.rbmq.listen_queue('active-queue', self.clear_active_queue,
                                     is_save=False)

        mf_handler = HandlerMFDocs(self.db, self.rbmq)
        self.active_manufactures = await mf_handler.get_active_mf()

        ships_handler = HandlerShipmentsDocs(self.db, self.rbmq)
        self.active_shipments = await ships_handler.get_active_shipments()

        # for debug
        # xml = await self.xml_from_file()
        # await self.rbmq.publication_task_json(xml, 'incoming-queue')

        is_err = False
        while True:
            try:
                await self.get_outgoing_docs()
                await self.get_incoming_docs()
                if is_err:
                    is_err = False
                    logger.info('utm_queue: Подключение к УТМ восстановлено.')
            except (TimeoutError, OSError, AMQPConnectionError,
                    aiohttp.client_exceptions.ServerDisconnectedError,
                    aiohttp.client_exceptions.ClientConnectorError,
                    asyncio.TimeoutError) as err:
                if not is_err:
                    logger.error(f'Ошибка в потоке парсинга(нет подключения к УТМ): {err}')
                    is_err = True
            except KeyboardInterrupt:
                await self.session.close()
                await self.rbmq.connection.close()
            await asyncio.sleep(1.8)


# legacy class
class Queue_utm:
    def __init__(self) -> None:
        pass

    @no_type_check
    def get_outgoing_docs(self, active_shipments):
        # collect all shipments
        response_out_docs = json.loads(requests.get(
            base_url + 'api/db/in/list?offset=0&limit=20').text)

        for row in response_out_docs['rows']:
            if row['docType'] == 'WayBill_v4':
                if row['uuid'] not in active_shipments.keys():
                    active_shipments[row['uuid']] = Shipment(
                        row['uuid'], requests.get(base_url + f'api/db/in/{row["id"]}').text)

    @no_type_check
    def get_incoming_docs(self, active_shipments, acts):
        # Pick up all the files associated with the shipment by uuid
        response_in_docs = json.loads(requests.get(
                            base_url + 'api/db/out/list?offset=0&limit=20').text)
        for row in response_in_docs['rows']:
            if row['docType'] == 'WayBillAct_v4':
                if row['id'] not in acts.keys():
                    acts[row['id']] = requests.get(base_url + f'api/db/out/{row["id"]}').text

            if row['replyId'] in active_shipments.keys():
                if row['id'] not in active_shipments[row['replyId']].incomings_xml.keys():
                    active_shipments[row['replyId']].incomings_xml[row['id']] = [
                                                            row['docType'],
                                                            requests.get(
                                                                base_url +
                                                                f'api/db/out/{row["id"]}').text]


@no_type_check
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
        except (TimeoutError, requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError, OSError) as err:
            if is_err is False:
                logger.error(f'Ошибка в потоке парсинга(нет подключения к УТМ): {err}')
                is_err = True
        locks.release()
        sleep(2)
