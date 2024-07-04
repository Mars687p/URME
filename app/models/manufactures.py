from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional

import asyncpg
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.logs import logger
from app.models.base_models import DocUtm
from app.utils import signal, writing_file_an_err
from base.database import Async_database
from custom_types.fixations import FixationManufactures
from custom_types.products import ProductManufactures, RawProductManufactures
from exeptions.parsing_error import ParsingError
from templates import query


class Manufacture(DocUtm):
    def __init__(self,
                 uuid: str,
                 outgoing_xml: str,
                 db: Async_database,
                 condition: str = 'Отправлено') -> None:
        super().__init__(uuid, outgoing_xml, db, condition)
        self.date_production: Optional[date] = None
        self.products: Dict[int, ProductManufactures] = {}
        self.fixation: FixationManufactures

    def parsing_outgoing_doc_v5(self) -> bool:
        if self.outgoing_xml is None:
            return False
        result = True
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')
        try:
            self._get_header(soup)
            self._get_footing(soup)
            self._get_products(soup, 'IdentityRes')
        except ParsingError as _ex:
            logger.error(_ex)
            result = False
            writing_file_an_err(self.outgoing_xml, 'Error outgoing parsing manufacture')

        self.outgoing_xml = ''
        return result

    def parsing_outgoing_doc_v6(self) -> bool:
        if self.outgoing_xml is None:
            return False
        result = True
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')
        try:
            self._get_header(soup)
            self._get_footing(soup)
            self._get_products(soup, 'IDENTITYPRODUCT')
        except ParsingError as _ex:
            logger.error(_ex)
            result = False
            writing_file_an_err(self.outgoing_xml, 'Error outgoing parsing manufacture')

        self.outgoing_xml = ''
        return result

    def parsing_incoming_doc(self, file_id: int) -> bool:
        """INCOMING DOCS"""
        result = True
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        try:
            # There are two types of response files: Ticket and FORM1REGINFO
            # Tickets are a response from the server and a local check
            # OperationResult - response from the server
            # Conclusion - local check
            if self.incomings_xml[file_id][0] == 'Ticket':
                self._process_ticket(soup)

            elif self.incomings_xml[file_id][0] == 'FORM1REGINFO':
                self._process_regform(soup)
        except ParsingError as _ex:
            logger.error(_ex)
            result = False
            writing_file_an_err(
                self.outgoing_xml,
                f'Error incoming parsing manufacture {self.incomings_xml[file_id][0]}')

        self.incomings_xml[file_id][1] = ''
        return result

    def _get_header(self, soup: BeautifulSoup) -> None:
        try:
            self.number = self._get_value_from_tag(soup, 'NUMBER')
            self.date = datetime.strptime(
                                        self._get_value_from_tag(soup,
                                                                 'Date'),
                                        '%Y-%m-%d').date()

            self.date_production = datetime.strptime(
                                        self._get_value_from_tag(soup,
                                                                 'ProducedDate'),
                                        '%Y-%m-%d').date()

            self.type_operation = self._get_value_from_tag(soup, 'rpp:Type')
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _get_footing(self,
                     soup: BeautifulSoup) -> None:
        header = soup.find('Header')
        if header is not None:
            try:
                self.footing = self._get_value_from_tag(header, 'Note')
                return None
            except ParsingError:
                pass
        self.footing = None

    def _get_products(self,
                      soup: BeautifulSoup,
                      tag_identity_type: str) -> None:
        try:
            for rows in soup.find_all('Position'):
                identity = int(rows.find('Identity').text)
                self.products[identity] = ProductManufactures({
                                'alcocode': int(rows.find('ProductCode').text.rstrip()),
                                'alcovolume': Decimal(rows.find('alcPercent').text),
                                'quantity': Decimal(rows.find('Quantity').text),
                                'party': rows.find('Party').text,
                                'form1': None,
                                'form2': None,
                                'raw': {}})
                self._get_raw_for_products(identity, rows, tag_identity_type)
        except AttributeError as _ex:
            raise ParsingError from _ex

    def _get_raw_for_products(self,
                              identity: int,
                              rows: Tag,
                              tag_identity_type: str) -> None:
        try:
            for item in rows.find_all('Resource'):
                # A dictionary of products with a position key.
                # Includes a dictionary of raw materials with keys
                # for the position of this raw material
                # products[keys_position][raw][raws_position] = {dict raw_product}
                self.products[identity]['raw'][int(item.find(tag_identity_type).text)] = \
                        RawProductManufactures({
                            'alcocode': int(item.find('AlcCode').text.rstrip()),
                            'form2': item.find('RegForm2').text,
                            'quantity': Decimal(item.find('Quantity').text),
                            'alcovolume': Decimal(item.find('AlcVolume').text),
                            })
        except AttributeError as _ex:
            raise ParsingError from _ex

    def _get_opration_result(self,
                             soup: BeautifulSoup) -> Optional[str]:
        tag_oper_result = soup.find('OperationResult')
        if tag_oper_result is None:
            return None
        try:
            return self._get_value_from_tag(tag_oper_result,
                                            'OperationResult')
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _process_ticket(self,
                        soup: BeautifulSoup) -> None:
        try:
            operation_result = self._get_opration_result(soup)
            if operation_result == 'Accepted':
                self.fixation = FixationManufactures({
                    'RegID': self._get_value_from_tag(soup, 'RegID'),
                    'fix_date': datetime.strptime(
                                                self._get_value_from_tag(soup,
                                                                         'OperationDate'),
                                                '%Y-%m-%dT%H:%M:%S.%f').date()})
                if self.condition != 'Зафиксировано в ЕГАИС':
                    self.condition = 'Принято ЕГАИС'

            elif operation_result is None:
                operation_result = self._get_value_from_tag(soup,
                                                            'Conclusion')
                if operation_result == 'Accepted':
                    return
                self.condition = 'Отклонено ЕГАИС'
                signal('reject')
            else:
                self.condition = 'Отклонено ЕГАИС'
                signal('reject')
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _process_regform(self,
                         soup: BeautifulSoup) -> None:
        try:
            for row in soup.find_all('wbr:Position'):
                pr = self.products[int(row.find('wbr:Identity').text)]
                pr['form1'] = row.find('wbr:InformF1RegId').text
                pr['form2'] = row.find('wbr:InformF2RegId').text
            self.condition = 'Зафиксировано в ЕГАИС'
        except AttributeError as _ex:
            raise ParsingError from _ex

    """
    ---------------------------------------------------------
    ------------------ WORK WITH DB -------------------------
    ---------------------------------------------------------
    """
    async def insert_db(self) -> bool:
        async with self.db.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                self.id_in_base = await con.fetchval(
                        query.insert_record_manufactures,
                        self.number,
                        self.condition,
                        self.uuid,
                        self.date,
                        self.date_production,
                        self.type_operation,
                        self.footing)

                for position, product in self.products.items():
                    try:
                        alcocode = await con.fetchval(query.select_product_async,
                                                      product['alcocode'])
                    except TypeError:
                        logger.error(f'Продукта {product["alcocode"]} нет в справочнике продукции')
                        return False

                    # mfed product
                    pr_id = await con.fetchval(
                                query.insert_manufactured_pr,
                                self.id_in_base,
                                alcocode,
                                position,
                                product['quantity'],
                                product['party'],
                                product['alcovolume'])

                    # raw
                    for pos in product['raw'].keys():
                        raw = product['raw'][pos]
                        try:
                            alcocode = await con.fetchval(query.select_product_async,
                                                          raw['alcocode'])
                        except asyncpg.exceptions.ForeignKeyViolationError as _ex:
                            logger.error(f'Продукта {raw["alcocode"]} \
                                         нет в справочнике продукции. {_ex}')
                            return False

                        await con.execute(query.insert_raw_pr,
                                          pr_id,
                                          alcocode,
                                          pos,
                                          raw['quantity'],
                                          raw['form2'])

        return True

    async def update_db(self) -> bool:
        async with self.db.pool.acquire() as con:
            con: asyncpg.connection.Connection  # type: ignore
            async with con.transaction():
                if self.condition == 'Зафиксировано в ЕГАИС':
                    await con.execute(query.update_mf_cond,
                                      self.condition,
                                      self.id_in_base)
                    for position, product in self.products.items():
                        await con.execute(query.update__mfed_products,
                                          product['form1'],
                                          product['form2'],
                                          self.id_in_base,
                                          position)

                elif self.condition == 'Отклонено ЕГАИС':
                    await con.execute(query.update_mf_cond,
                                      self.condition,
                                      self.id_in_base)

                if self.fixation != {}:
                    await con.execute(
                            query.update__mf_regdata,
                            self.fixation['RegID'],
                            self.fixation['fix_date'],
                            self.id_in_base)
                    if self.condition == 'Принято ЕГАИС':
                        await con.execute(query.update_mf_cond, self.condition, self.id_in_base)

        logger.info(
                f"DB.update manufactures: {self.condition}, {self.number}, id: {self.id_in_base}")
        return True
