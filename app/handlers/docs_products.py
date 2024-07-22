
from typing import TYPE_CHECKING

from app.models.products import Product
from custom_types.rabbit import RabbitMessageQueueUTM

if TYPE_CHECKING:
    from base.database import Async_database


class HandlerProductsDocs:
    def __init__(self, db: 'Async_database') -> None:
        self.db = db

    async def processing_in_products(self, msg: RabbitMessageQueueUTM) -> bool:
        result = True
        pr = Product(uuid=msg['uuid'],
                     outgoing_xml=msg['xml'],
                     db=self.db)
        pr.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]

        # Checking if the file is parsed
        if pr.incomings_xml[msg['id_doc']][1] != '':
            pr.parsing_incoming_doc(msg['id_doc'])
            result = await pr.insert_db()

        return result
