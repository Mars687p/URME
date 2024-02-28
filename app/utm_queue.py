import json
import requests
import asyncio, aiohttp
from aiormq.exceptions import AMQPConnectionError
from time import sleep
from threading import RLock
from aio_pika.abc import AbstractIncomingMessage

from app.shipments import Shipment, Handler_ships_docs
from app.configuration import get_url_utm
from app.manufactures import Manufacture, Handler_mf_docs
from app.products import Handler_prod_docs
from app.rabbit import Rabbit
from app.services import error_parsing
from app.logs import logger
from base.database import Async_database


base_url: str = get_url_utm()
TYPE_ACTS = ('WayBillAct_v4', 'QueryRejectRepProduced', 'ReplyForm1',)
TYPE_PRODUCT_ACTS = ('ReplyAP', 'ReplySSP', 'ReplySpirit', 'ReplyAP_v2', 'ReplyAP_v3', 'ReplySSP_v2', 'ReplySpirit_v2')



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
        except (TimeoutError, requests.exceptions.ConnectTimeout, 
                              requests.exceptions.ConnectionError, OSError) as err:
            if is_err == False:
                logger.error(f'Ошибка в потоке парсинга(нет подключения к УТМ): {err}')
                is_err = True
        locks.release()
        sleep(2)



#new queue tracking method 
class Aio_utm_queue:
    def __init__(self, ex_name) -> None:
        self.ex_name = ex_name
        self.db = Async_database('postgres')
        self.active_shipments: dict = {}
        self.active_manufactures: dict = {}
        self.acts: dict = {}

    async def parsing_in_queue(self, row):
        try:
            # shipments
            if row['replyId'] in self.active_shipments.keys():
                if row['id'] not in self.active_shipments[row['replyId']].incomings_xml.keys():
                                        # id_doc, replyid(uuid), type_doc, type_queue, type_file
                    await self.get_xml_doc(row['id'], row['replyId'], 'shipments', 0, row['docType'])
                    self.active_shipments[row['replyId']].incomings_xml[row['id']] = None
            elif row['docType'] == 'WayBillAct_v4':
                if row['id'] not in self.acts.keys():
                    await self.get_xml_doc(row['id'], row['replyId'], 'shipments', 0, row['docType'])
                    self.acts[row['id']] = 0
            
            # manufactures 
            elif row['replyId'] in self.active_manufactures.keys():
                    if row['id'] not in self.active_manufactures[row['replyId']].incomings_xml.keys():
                                            # id_doc, replyid(uuid), type_doc, type_queue, type_file
                        await self.get_xml_doc(row['id'], row['replyId'], 'manufactures', 0, row['docType'])
                        self.active_manufactures[row['replyId']].incomings_xml[row['id']] = None
            elif row['docType'] == 'QueryRejectRepProduced':
                if row['id'] not in self.acts.keys():
                    await self.get_xml_doc(row['id'], row['replyId'], 'manufactures', 0)
                    self.acts[row['id']] = 0
            elif row['docType'] == 'ReplyForm1':
                if row['id'] not in self.acts.keys():
                    await self.get_xml_doc(row['id'], row['replyId'], 'manufactures', 0, row['docType'])
                    self.acts[row['id']] = 0
            
            # products
            elif row['docType'] in TYPE_PRODUCT_ACTS:
                if row['id'] not in self.acts.keys():
                    await self.get_xml_doc(row['id'], row['replyId'], 'product_ref', 0, row['docType'])
                    self.acts[row['id']] = 0
            
            #for unknown files, del before release
            else:
                if row['docType'] not in ['Ticket', 'FORM2REGINFO', 'FORM1REGINFO']:
                    if row['id'] not in self.acts.keys():
                        await self.get_xml_doc(row['id'], row['replyId'], 'unknown_xml', 0, row['docType'])
                        self.acts[row['id']] = 999
        except KeyError:
            error_parsing('', 'Keyerror in incoming_queue, aio_utm')

    @logger.catch
    async def get_xml_doc(self, id_doc: int, uuid: str, type_doc: str, 
                                        queue_type: bool, type_file=None):
        async with aiohttp.ClientSession() as session:
            #queue_type = 1 - outgoing | 0 - incoming
            if queue_type:                    
                async with session.get(base_url + f'api/db/in/{id_doc}') as doc:
                    doc = await doc.text()
                    await self.rbmq.publication_task_json({
                                                "type_doc": type_doc,
                                                "uuid": uuid,
                                                "id_doc": id_doc,
                                                "type_file": type_file,
                                                "xml": doc,}, "outgoing-queue")
            else:
                async with session.get(base_url + f'api/db/out/{id_doc}') as doc:
                    doc = await doc.text()
                    await self.rbmq.publication_task_json({
                                                "type_doc": type_doc,
                                                "uuid": uuid,
                                                "id_doc": id_doc,
                                                "type_file": type_file,
                                                "xml": doc,}, "incoming-queue")
            
    logger.catch
    async def get_outgoing_docs(self):
        #collect all shipments 
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url + 'api/db/in/list?offset=0&limit=40') as queue_out:
                queue_out = json.loads(await queue_out.text())
                for row in queue_out['rows']:
                    if row['docType'] == 'WayBill_v4':
                        if row['uuid'] not in self.active_shipments.keys():
                            await self.get_xml_doc(row['id'], row['uuid'], 'shipments', 1)
                            self.active_shipments[row['uuid']] = Shipment(row['uuid'], None)
                    
                    if row['docType'] == 'RepProducedProduct_v5':
                        if row['uuid'] not in self.active_manufactures.keys():
                            await self.get_xml_doc(row['id'], row['uuid'], 'manufactures', 1)
                            self.active_manufactures[row['uuid']] = Manufacture(row['uuid'], None)
                    
    logger.catch
    async def get_incoming_docs(self):
        #Pick up all the files associated with the shipment by uuid
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url + 'api/db/out/list?offset=0&limit=40') as queue_in:
                queue_in = json.loads(await queue_in.text())
                await asyncio.gather(*[self.parsing_in_queue(row) for row in queue_in['rows']])
    
    @logger.catch
    async def clear_active_queue(self, message):
        msg = json.loads(message.body.decode())
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
                await asyncio.sleep(1200)
                del self.acts[msg['id_doc']]
            else:
                #for unknown files, del before release
                await asyncio.sleep(1200)
                del self.acts[msg['id_doc']]
        except KeyError:
            pass

    async def xml_from_file(self):
        with open(r'E:\progs\Autoshipments\failed_parse\3.xml', 'r', encoding='utf-8') as f:
            file = f.read()
        return {"xml": file,
                "type_doc": "shipments",
                "uuid": "121212312",
                "id_doc": "1",
                "type_file": "WayBillAct_v4"}
    
    @logger.catch
    async def run_doc_picker(self):
        await self.db.get_connection()
        active_mf = Handler_mf_docs(self.db)
        self.active_manufactures = await active_mf.get_active_mf()

        active_ships = Handler_ships_docs(self.db)
        self.active_shipments = await active_ships.get_active_shipments()

        self.rbmq = Rabbit(self.ex_name)
        await self.rbmq.start()
        await self.rbmq.listen_queue('active-queue', self.clear_active_queue, False)
        
        # for debug
        # xml = await self.xml_from_file()
        # await self.rbmq.publication_task_json(xml, 'incoming-queue', True)
        is_err = False
        while True:
            try:
                await self.get_outgoing_docs()
                await self.get_incoming_docs()
                if is_err:
                    await self.rbmq.listen_queue('active-queue', self.clear_active_queue, False)
                    is_err = False
                    logger.info('utm_queue: Подключение к УТМ восстановлено.')
            except (TimeoutError, OSError, AMQPConnectionError, 
                    aiohttp.client_exceptions.ServerDisconnectedError,
                    asyncio.TimeoutError) as err:
                if is_err == False:
                    logger.error(f'Ошибка в потоке парсинга(нет подключения к УТМ): {err}')
                    is_err = True
            except KeyboardInterrupt:
                await self.rbmq.connection.close()
            await asyncio.sleep(2,2) 



"""
----------------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------ CONSUMER UTM QUEUE --------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------------------------------------
"""



class Consumer_utm_queue:
    def __init__(self, ex_name) -> None:
        self.rbmq = Rabbit(ex_name)
        self.db = Async_database('postgres')
        self.ships = Handler_ships_docs(self.db)
        self.mf = Handler_mf_docs(self.db)
        self.sem = asyncio.Semaphore()

    @logger.catch
    async def outgoing_queue(self, message: AbstractIncomingMessage):
        async with message.process(ignore_processed=True):
            msg = json.loads(message.body.decode())
            if msg['type_doc'] == 'shipments':
                async with self.sem:
                    result_parsing = await self.ships.processing_out_shipments(msg)

            if msg['type_doc'] == 'manufactures':
                async with self.sem:
                    result_parsing = await self.mf.processing_out_mf(msg)
                
            if result_parsing:
                await message.ack()
            else:
                await message.reject(requeue=False)

    @logger.catch
    async def incoming_queue(self, message: AbstractIncomingMessage):
        async with message.process(ignore_processed=True):
            msg = json.loads(message.body.decode())
            result_parsing = False

            if msg['type_doc'] == 'shipments':
                async with self.sem:
                    result_parsing = await self.ships.processing_in_shipments(msg, self.rbmq)

            elif msg['type_doc'] == 'manufactures':
                async with self.sem:
                    result_parsing = await self.mf.processing_in_mf(msg, self.rbmq)
            
            elif msg['type_doc'] == 'product_ref':
                async with self.sem:
                    prod = Handler_prod_docs(self.db)
                    result_parsing = await prod.processing_in_products(msg)
                await self.rbmq.publication_task_json({'type_file': msg['type_file'], 
                    'uuid': msg['uuid'], 
                    'id_doc': msg['id_doc']}, 'active-queue', False) 
                    
            elif msg['type_doc'] == 'unknown_xml':
                error_parsing(msg['xml'], msg['type_file'])
                await self.rbmq.publication_task_json({'type_file': msg['type_file'], 
                    'uuid': msg['uuid'], 
                    'id_doc': msg['id_doc']}, 'active-queue', False) 
                logger.warning('Unknown type file')            
            
            if result_parsing:
                await message.ack()
            else:
                error_parsing(msg['xml'], f'Отмененный файл incoming {msg["type_doc"]} - {msg["type_file"]}')
                await message.reject(requeue=False)
    
    async def start(self):
        try:
            await self.db.get_connection()
            await self.mf.get_active_mf()
            await self.ships.get_active_shipments()
            await self.rbmq.start()

            await self.rbmq.listen_queue('outgoing-queue', self.outgoing_queue)
            await self.rbmq.listen_queue('incoming-queue', self.incoming_queue)
            while True:
                try:
                    await asyncio.sleep(5)
                    if self.rbmq.read_channel.is_closed:
                        logger.warning('Нет подключения к rabbit в Consumers')
                        await self.rbmq.listen_queue('outgoing-queue', self.outgoing_queue)
                        await self.rbmq.listen_queue('incoming-queue', self.incoming_queue)
                        logger.info('Подключение к rabbit в Consumers восстановлено.')
                except Exception as _ex:
                    logger.error('Неопознанная ошибка в Consumers ', _ex)

        except KeyboardInterrupt:
            await self.rbmq.connection.close()