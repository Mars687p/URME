from typing import Dict

from app.handlers.base_handlers import Handler
from app.logs import logger
from app.models.acts import ShipmentActs
from app.models.shipments import Shipment
from app.rabbit import Rabbit
from app.utils import writing_file_an_err
from base.database import Async_database
from custom_types.rabbit import RabbitMessageQueueUTM
from templates import query


# aio + rabbitmq parsing
# The processing functions return a tuple of the form:
# (Whether successfully processed; if so, the processed object)
class HandlerShipmentsDocs(Handler):
    def __init__(self, db: Async_database, rbmq: Rabbit) -> None:
        super().__init__(db, rbmq)
        self.active_ships: dict[str, Shipment] = {}

    async def get_active_shipments(self) -> Dict:
        active_shipments: dict = {}
        async with self.db.pool.acquire() as con:
            rows = [i for i in await con.fetch(query.select_active_shipments)]
            for item in rows:
                active_shipments[str(item['uuid'])] = Shipment(str(item['uuid']),
                                                               '',
                                                               self.db,
                                                               item['condition'])
                active_shipments[str(item['uuid'])].id_in_base = item['id']
                active_shipments[str(item['uuid'])].number = item['num']
                response = await con.fetch(query.select_cart_pr_async, item['id'])
                for product in response:
                    active_shipments[str(item['uuid'])].products[
                                        product['positions']] = {'form2_old': product['form2_old']}
        self.active_ships = active_shipments
        return self.active_ships

    async def processing_outgoing(self, msg: RabbitMessageQueueUTM) -> bool:
        if msg['uuid'] not in self.active_ships.keys():
            if msg['type_file'] == 'WayBill_v4':
                self.active_ships[msg['uuid']] = Shipment(
                                                        msg['uuid'],
                                                        msg['xml'],
                                                        self.db)
                shipment = self.active_ships[msg['uuid']]
                result_parsing = shipment.parsing_outgoing_doc_v4()
                if result_parsing:
                    result = await shipment.insert_shipment()

            else:
                logger.error(f"Неизвестный тип файла - {msg['type_file']}")
                result = False

            return result
        return True

    async def processing_incoming(self, msg: RabbitMessageQueueUTM) -> bool:
        if msg['type_file'] in ['FORM2REGINFO', 'Ticket']:
            result = await self._handle_shipments(msg)

        elif msg['type_file'] == 'WayBillAct_v4':
            result = await self._handle_waybill_act(msg)
        else:
            writing_file_an_err(msg['xml'],
                                f"Неопознанный тип файла в ships {msg['type_file']}")
            logger.error(f"Неизвестный тип файла - {msg['type_file']}")
            return False

        return result

    async def _handle_shipments(self, msg: RabbitMessageQueueUTM) -> bool:
        result = True
        try:
            ship = self.active_ships[msg['uuid']]
        except KeyError:
            if msg['type_file'] == 'Ticket':
                return True
            return False

        ship.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]

        # Checking if the file is parsed
        if ship.incomings_xml[msg['id_doc']][1] != '':
            condition = ship.condition
            result = ship.parsing_incoming_doc(msg['id_doc'])
            if result:
                if ship.condition != condition:
                    result = await ship.update_shipment()

            if ship.condition in ['Принято ЕГАИС', 'Отклонено ЕГАИС']:
                await self.rbmq.publication_task_json(
                            RabbitMessageQueueUTM({
                                'type_file': 'FORM2REGINFO',
                                'uuid': msg['uuid'],
                                'id_doc': msg['id_doc'],
                                'type_doc': None}),
                            'active-queue',
                            False)
                del self.active_ships[msg['uuid']]

        return result

    async def _handle_waybill_act(self, msg: RabbitMessageQueueUTM) -> bool:
        act = ShipmentActs(
                            uuid=msg['uuid'],
                            incoming_xml=msg['xml'],
                            db=self.db)
        state, ttn, positions, date_act = act.parsing_ships_acts()
        result = await act.update_waybill_act(state, ttn, positions, date_act)
        await self.rbmq.publication_task_json(
                            RabbitMessageQueueUTM({
                                'type_file': msg['type_file'],
                                'uuid': msg['uuid'],
                                'id_doc': msg['id_doc'],
                                'type_doc': None}),
                            'active-queue',
                            False)
        return result
