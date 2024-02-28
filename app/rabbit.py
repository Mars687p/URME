import json
import asyncio
from aio_pika import connect_robust, Message, ExchangeType, DeliveryMode
from aio_pika.abc import AbstractRobustConnection, AbstractChannel

from app.configuration import get_data_connection_rabbit
from app.logs import logger


rabbit = get_data_connection_rabbit()

class Rabbit:
    def __init__(self, name_ex) -> None:
        self.name_ex = name_ex
        self.rabbit = get_data_connection_rabbit()

    async def get_connection_rb(self) -> AbstractRobustConnection:
        return await connect_robust(
        f'amqp://{self.rabbit["user"]}:{self.rabbit["password"]}@{self.rabbit["name_pc"]}')
    
    async def get_q_ex(self, name_q, is_save, name_ex=None):
        if name_ex == None: name_ex = self.name_ex
        exchange = await self.publisher_channel.declare_exchange(name_ex, 
                                            ExchangeType.DIRECT, durable=True,)
        if is_save:
            queue = await self.publisher_channel.declare_queue(name_q, durable=True,
                                            arguments={'x-dead-letter-exchange': 'rej-ex',
                                                       'x-dead-letter-routing-key': 'rej-q'})
        else:
            queue = await self.publisher_channel.declare_queue(name_q, durable=True,)
        await queue.bind(exchange)
        return exchange, queue

    @logger.catch
    async def publication_task_json(self, body, name_q, is_save=True) -> None:
        await self.get_q_ex('rej-q', True, 'rej-ex')
        exchange, _ = await self.get_q_ex(name_q, is_save)
        msg = Message(body=json.dumps(body).encode(), 
                      delivery_mode=DeliveryMode.PERSISTENT,)
        await exchange.publish(msg, routing_key=name_q)
    
    @logger.catch
    async def listen_queue(self, name_q, func, is_save=True) -> None:
        await self.get_q_ex('rej-q', True, 'rej-ex')
        _, queue = await self.get_q_ex(name_q, is_save)
        await self.read_channel.set_qos(prefetch_count=5)
        await queue.consume(func)

    async def start(self):
        self.connection = await self.get_connection_rb()
        self.publisher_channel = await self.connection.channel()
        self.read_channel = await self.connection.channel()