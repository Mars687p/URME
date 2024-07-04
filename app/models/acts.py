from datetime import date, datetime
from typing import Dict, Optional

import asyncpg
from bs4 import BeautifulSoup

from app.logs import logger
from app.models.base_models import ActUtm
from app.utils import writing_file_an_err
from base.database import Async_database
from templates import query


class ShipmentActs(ActUtm):
    def __init__(self,
                 uuid: str,
                 db: Async_database,
                 outgoing_xml: str = '',
                 incoming_xml: str = '') -> None:
        super().__init__(uuid, db, outgoing_xml)
        self.incoming_xml = incoming_xml

    def parsing_ships_acts(self) -> tuple:
        soup = BeautifulSoup(self.incoming_xml, 'lxml-xml')
        try:
            date_act = datetime.strptime(soup.find('ActDate').text,  # type: ignore
                                         '%Y-%m-%d').date()
            ttn_reg = soup.find('WBRegId').text  # type: ignore
            is_accept = soup.find('IsAccept').text  # type: ignore
        except AttributeError:
            ttn_reg = None
            is_accept = None
        positions: Dict[str, float] = {}

        if is_accept == 'Accepted':
            state = 'Проведено'
        elif is_accept == 'Differences':
            state = 'Проведено частично'
            for position in soup.find_all('Position'):
                positions[position.find('InformF2RegId').text] = float(
                                                        position.find('RealQuantity').text)
        else:
            state = 'Распроведено'
        return (state, ttn_reg, positions, date_act)

    async def update_waybill_act(self,
                                 condition: str,
                                 ttn: str,
                                 positions: dict,
                                 date_act: date) -> bool:
        async with self.db.pool.acquire() as con:
            async with con.transaction():
                if condition == 'Проведено частично':
                    for form2, position in positions.items():
                        await con.execute(query.update_cart_product_partly_async, position, form2)
                await con.execute(query.update_shipment_partly_async, condition, date_act, ttn)
        logger.info(f"DB.update act: {condition}, {ttn}, {date_act}, {positions}")
        return True


class ManufacturesActs(ActUtm):
    def __init__(self,
                 uuid: str,
                 db: Async_database,
                 outgoing_xml: str = '',
                 incoming_xml: str = '') -> None:
        super().__init__(uuid, db, outgoing_xml)
        self.incoming_xml = incoming_xml

    def parsing_mf_acts(self) -> Optional[list]:
        soup = BeautifulSoup(self.incoming_xml, 'lxml-xml')
        try:
            date_act = datetime.strptime(soup.find('TicketDate').text,  # type: ignore
                                         '%Y-%m-%d').date()
            reg_id = soup.find('RegId').text  # type: ignore
            is_accept = soup.find('OperationResult').text  # type: ignore
        except AttributeError:
            reg_id = None
            is_accept = None
        positions: dict = {}

        if is_accept == 'Accepted':
            state = 'Распроведено'
            return [state, reg_id, positions, date_act]

        writing_file_an_err(self.incoming_xml, 'from act mf: Неизвестный формат')
        return None

    def parsing_mf_wbf_num(self) -> tuple:
        try:
            soup = BeautifulSoup(self.incoming_xml, 'lxml-xml')
            date_mf = datetime.strptime(soup.find('OriginalDocDate').text,  # type: ignore
                                        '%Y-%m-%d').date()
            num_mf = soup.find('OriginalDocNumber').text  # type: ignore
            wbf_num = soup.find('EGAISNumber').text  # type: ignore
            return (wbf_num, date_mf, num_mf)
        except AttributeError as _ex:
            writing_file_an_err(self.incoming_xml, 'from act')
            raise AttributeError from _ex

    async def update_db_mf_acts(self,
                                state: str,
                                reg_id: str,
                                positions: str,
                                date_act: date) -> bool:
        try:
            async with self.db.pool.acquire() as con:
                await con.execute(
                                query.update_mf_act,
                                state,
                                date_act,
                                reg_id)
        except asyncpg.exceptions as _ex:
            writing_file_an_err(self.incoming_xml, f'Ошибка добавления БД wbf mf: {_ex}')
            return False
        logger.info(f"DB.update mf act: {state}, {reg_id}, {date_act}, {positions}")
        return True

    async def update_db_mf_wbf_num(self,
                                   fix_number: str,
                                   date_production: date,
                                   num: int) -> bool:
        await self.db.update_sql(query.update_mf_wbf_num,
                                 fix_number,
                                 date_production,
                                 num)
        return True
