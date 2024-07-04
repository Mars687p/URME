from abc import abstractmethod
from typing import Any

from app.rabbit import Rabbit
from base.database import Async_database
from custom_types.rabbit import RabbitMessageQueueUTM


class Handler:
    def __init__(self, db: Async_database, rbmq: Rabbit) -> None:
        self.db = db
        self.rbmq = rbmq

    @abstractmethod
    async def processing_outgoing(self, msg: RabbitMessageQueueUTM) -> Any:
        ...

    @abstractmethod
    async def processing_incoming(self, msg: RabbitMessageQueueUTM) -> Any:
        ...
