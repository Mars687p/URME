from typing import Dict

from app.handlers.base_handlers import Handler
from app.logs import logger
from app.models.acts import ManufacturesActs
from app.models.manufactures import Manufacture
from app.rabbit import Rabbit
from base.database import Async_database
from custom_types.products import ProductManufactures
from custom_types.rabbit import RabbitMessageQueueUTM
from templates import query


class Handler_mf_docs(Handler):
    def __init__(self, db: Async_database, rbmq: Rabbit) -> None:
        super().__init__(db, rbmq)
        self.active_mf: Dict[str, Manufacture] = {}

    async def get_active_mf(self) -> Dict[str, Manufacture]:
        mf: Dict[str, Manufacture] = {}
        async with self.db.pool.acquire() as con:
            rows = [i for i in await con.fetch(query.select_active_mf)]
            for item in rows:
                uuid = str(item['uuid'])
                mf[uuid] = Manufacture(uuid, '', item['condition'])
                mf[uuid].id_in_base = item['id']
                response = await con.fetch(query.select_mf_product_async, item['id'])
                for product in response:
                    mf[uuid].products[product['positions']] = ProductManufactures({
                        'alcocode': None,  # type: ignore
                        'form1': None,
                        'alcovolume': None,  # type: ignore
                        'form2': None,
                        'party': None,
                        'quantity': None,
                        'raw': {}
                    })
        self.active_mf = mf
        return self.active_mf

    async def processing_outgoing(self, msg: RabbitMessageQueueUTM) -> bool:
        result = True
        if msg['uuid'] not in self.active_mf.keys():
            self.active_mf[msg['uuid']] = Manufacture(uuid=msg['uuid'],
                                                      outgoing_xml=msg['xml'],
                                                      db=self.db)
            mf: Manufacture = self.active_mf[msg['uuid']]

            if msg['type_file'] == 'm_v5':
                result_parsing = mf.parsing_outgoing_doc_v5()
            elif msg['type_file'] == 'm_v6':
                result_parsing = mf.parsing_outgoing_doc_v6()
            else:
                logger.error(f"Неизвестный тип файла - {msg['type_file']}")
                result_parsing = False

            if not result_parsing:
                return result_parsing

            result = await mf.insert_db()
        return result

    async def processing_incoming(self, msg: RabbitMessageQueueUTM) -> bool:
        if msg['type_file'] in ['FORM1REGINFO', 'Ticket']:
            result = await self._handle_mf(msg)

        elif msg['type_file'] == 'QueryRejectRepProduced':
            result = await self._handle_act_query_reject_rep(msg)

        elif msg['type_file'] == 'ReplyForm1':
            result = await self._handle_act_reply_form1(msg)
        else:
            result = False

        return result

    async def _handle_act_reply_form1(self, msg: RabbitMessageQueueUTM) -> bool:
        act = ManufacturesActs(
                    uuid=msg['uuid'],
                    incoming_xml=msg['xml'],
                    db=self.db)

        data = act.parsing_mf_wbf_num()
        result = await act.update_db_mf_wbf_num(*data)
        await self.rbmq.publication_task_json(RabbitMessageQueueUTM({
                            'type_file': msg['type_file'],
                            'uuid': msg['uuid'],
                            'id_doc': msg['id_doc'],
                            'type_doc': None
                        }),
                        'active-queue',
                        False)
        return result

    async def _handle_act_query_reject_rep(self, msg: RabbitMessageQueueUTM) -> bool:
        act = ManufacturesActs(
                    uuid=msg['uuid'],
                    incoming_xml=msg['xml'],
                    db=self.db)
        result_parsing = act.parsing_mf_acts()
        if result_parsing is None:
            return False
        state, reg_id, positions, date_act = result_parsing

        result = await act.update_db_mf_acts(state, reg_id, positions, date_act)
        await self.rbmq.publication_task_json(
                            RabbitMessageQueueUTM({
                                'type_file': msg['type_file'],
                                'uuid': msg['uuid'],
                                'id_doc': msg['id_doc'],
                                'type_doc': None
                            }),
                            'active-queue',
                            False)
        if not result:
            logger.error('Ошибка добавления БД: mf act')
        return result

    async def _handle_mf(self,  msg: RabbitMessageQueueUTM) -> bool:
        # if the Keyerror is the Ticket file type, then a more important REGFORM1
        # file was processed before it and you can not process it further
        result = True
        try:
            mf = self.active_mf[msg['uuid']]
        except KeyError:
            if msg['type_file'] == 'Ticket':
                return True
            return False

        mf.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]

        # Checking if the file is not parsed
        if mf.incomings_xml[msg['id_doc']][1] != '':
            result = mf.parsing_incoming_doc(msg['id_doc'])
            if result:
                result = await mf.update_db()

            # fixation get in Ticket, condition == 'Зафиксировано в ЕГАИС' in REGFORM1
            if (mf.fixation != {} and mf.condition == 'Зафиксировано в ЕГАИС') or \
                    mf.condition == 'Отклонено ЕГАИС':
                await self.rbmq.publication_task_json(
                                RabbitMessageQueueUTM({
                                    'type_file': 'FORM1REGINFO',
                                    'uuid': msg['uuid'],
                                    'id_doc': msg['id_doc'],
                                    'type_doc': None}),
                                'active-queue',
                                False)
                del self.active_mf[msg['uuid']]

        return result
