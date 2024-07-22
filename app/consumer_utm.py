import asyncio
import json
from typing import NoReturn

from aio_pika.abc import AbstractIncomingMessage

from app.handlers.docs_manufactures import HandlerMFDocs
from app.handlers.docs_products import HandlerProductsDocs
from app.handlers.docs_shipments import HandlerShipmentsDocs
from app.logs import logger
from app.rabbit import Rabbit
from app.utils import writing_file_an_err
from base.database import Async_database
from custom_types.rabbit import RabbitMessageQueueUTM

"""
-------------------------------------------------------------------------------------------------
------------------------------------ CONSUMER UTM QUEUE -----------------------------------------
-------------------------------------------------------------------------------------------------
"""


class Consumer_utm_queue:
    def __init__(self, ex_name: str) -> None:
        self.rbmq = Rabbit(ex_name)
        self.db = Async_database('postgres')
        self.ships = HandlerShipmentsDocs(self.db, self.rbmq)
        self.mf_handler = HandlerMFDocs(self.db, self.rbmq)
        self.prod_handler = HandlerProductsDocs(self.db)
        self.sem = asyncio.Semaphore()

    @logger.catch
    async def outgoing_queue(self, message: AbstractIncomingMessage) -> None:
        async with message.process(ignore_processed=True):
            msg = json.loads(message.body.decode())
            if msg['type_doc'] == 'shipments':
                async with self.sem:
                    result_parsing = await self.ships.processing_outgoing(msg)

            if msg['type_doc'] == 'manufactures':
                async with self.sem:
                    result_parsing = await self.mf_handler.processing_outgoing(msg)

            if result_parsing:
                await message.ack()
            else:
                await message.reject(requeue=False)

    @logger.catch
    async def incoming_queue(self, message: AbstractIncomingMessage) -> None:
        async with message.process(ignore_processed=True):
            msg = RabbitMessageQueueUTM(json.loads(message.body.decode()))  # type: ignore
            result_operation = True
            async with self.sem:
                if msg['type_doc'] == 'shipments':
                    result_operation = await self.ships.processing_incoming(msg)

                elif msg['type_doc'] == 'manufactures':
                    result_operation = await self.mf_handler.processing_incoming(msg)

                elif msg['type_doc'] == 'product_ref':
                    result_operation = await self.prod_handler.processing_in_products(msg)
                    await self.rbmq.publication_task_json(RabbitMessageQueueUTM({
                                                'type_file': msg['type_file'],
                                                'uuid': msg['uuid'],
                                                'id_doc': msg['id_doc'],
                                                'type_doc': None
                                            }),
                                            'active-queue',
                                            False)

                else:
                    writing_file_an_err(msg['xml'], msg['type_file'])
                    await self.rbmq.publication_task_json(RabbitMessageQueueUTM({
                                                'type_file': msg['type_file'],
                                                'uuid': msg['uuid'],
                                                'id_doc': msg['id_doc'],
                                                'type_doc': None
                                            }),
                                            'active-queue',
                                            False)

            if result_operation:
                await message.ack()
            else:
                writing_file_an_err(
                    msg['xml'],
                    f'Отмененный файл incoming {msg["type_doc"]} - {msg["type_file"]}')
                await message.reject(requeue=False)

    async def start(self) -> NoReturn:
        await self.db.get_connection()
        await self.mf_handler.get_active_mf()
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
            except KeyboardInterrupt:
                await self.rbmq.connection.close()
