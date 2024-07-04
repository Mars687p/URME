import json
from typing import Callable, Optional

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust
from aio_pika.abc import (AbstractExchange, AbstractQueue,
                          AbstractRobustConnection)
from aiormq.exceptions import AMQPConnectionError

from app.configuration import get_data_connection_rabbit
from app.logs import logger
from app.utils import writing_file_an_err
from custom_types.rabbit import RabbitMessageQueueUTM

rabbit = get_data_connection_rabbit()


class Rabbit:
    def __init__(self, name_ex: str) -> None:
        self.name_ex = name_ex
        self.rabbit = get_data_connection_rabbit()

    async def get_connection_rb(self) -> AbstractRobustConnection:
        return await connect_robust(
            f'amqp://{self.rabbit["user"]}:{self.rabbit["password"]}@{self.rabbit["name_pc"]}')

    async def get_q_ex(self,
                       name_q: str,
                       name_ex: Optional[str] = None,
                       is_save: Optional[bool] = True) -> tuple[AbstractExchange, AbstractQueue]:
        if name_ex is None:
            name_ex = self.name_ex
        exchange = await self.publisher_channel.declare_exchange(
                                            name_ex,
                                            ExchangeType.DIRECT,
                                            durable=True,)
        if is_save:
            queue = await self.publisher_channel.declare_queue(
                                            name_q,
                                            durable=True,
                                            arguments={'x-dead-letter-exchange': 'rej-ex',
                                                       'x-dead-letter-routing-key': 'rej-q'})
        else:
            queue = await self.publisher_channel.declare_queue(name_q, durable=True,)

        await queue.bind(exchange)
        return exchange, queue

    @logger.catch
    async def publication_task_json(self,
                                    body: RabbitMessageQueueUTM,
                                    name_q: str,
                                    is_save: bool = True) -> None:
        """is_save is needed to indicate whether to save messages to disk or not"""
        try:
            await self.get_q_ex('rej-q', 'rej-ex')
            exchange, _ = await self.get_q_ex(name_q, is_save=is_save)
            msg = Message(body=json.dumps(body).encode(),
                          delivery_mode=DeliveryMode.PERSISTENT,)
            await exchange.publish(msg, routing_key=name_q)
        except AMQPConnectionError:
            writing_file_an_err(body['xml'], 'Ошибка добавления в rabbit')

    @logger.catch
    async def listen_queue(self,
                           name_q: str,
                           func: Callable,
                           is_save: bool = True) -> None:
        await self.get_q_ex('rej-q', 'rej-ex')
        _, queue = await self.get_q_ex(name_q, is_save=is_save)
        await self.read_channel.set_qos(prefetch_count=5)
        await queue.consume(func)

    async def start(self) -> None:
        self.connection = await self.get_connection_rb()
        self.publisher_channel = await self.connection.channel()
        self.read_channel = await self.connection.channel()
