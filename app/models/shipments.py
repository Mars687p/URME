from datetime import datetime
from decimal import Decimal
from time import sleep
from typing import Dict, no_type_check

from bs4 import BeautifulSoup

from app.logs import logger
from app.models.base_models import DocUtm
from app.utils import signal, writing_file_an_err
from base.database import Async_database
from custom_types.counterparty import Counterparty
from custom_types.fixations import FixationShipments
from custom_types.products import ProductShipments
from custom_types.transports import TransportShipments
from exeptions.parsing_error import ParsingError
from templates import query


class Shipment(DocUtm):
    def __init__(self,
                 uuid: str,
                 outgoing_xml: str,
                 db: Async_database,
                 condition: str = 'Отправлено') -> None:
        super().__init__(uuid, outgoing_xml, db, condition)
        self.fixation: FixationShipments
        self.transport: TransportShipments
        self.client = Counterparty({
                            'fsrar_id': None,
                            'name': None,
                            'address': None,
                            'INN': None,
                            'KPP': None,
        })
        self.products: Dict[str, ProductShipments] = {}

    def parsing_outgoing_doc_v4(self) -> bool:
        if self.outgoing_xml is None:
            return False

        result = True
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')
        try:
            self.number = int(self._get_value_from_tag(soup, 'wb:NUMBER'))
            self.date = datetime.strptime(self._get_value_from_tag(soup, 'wb:Date'),
                                          '%Y-%m-%d').date()
            self._get_client(soup)
            self._get_footing(soup)
            self._get_transport_section(soup)
            self._get_products(soup)
        except ParsingError as _ex:
            logger.error(_ex)
            result = False
            writing_file_an_err(self.outgoing_xml, 'Error outgoing parsing shipments')

        if self.uuid == 'repeat':
            return result
        self.outgoing_xml = ''
        return result

    def parsing_incoming_doc(self, file_id: int) -> bool:
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        # There are two types of response files: Ticket and FORM2REGINFO
        # Tickets are a response from the server and a local check
        # tc:OperationResult - response from the server
        # tc:Conclusion - local check
        result = True
        try:
            if self.incomings_xml[file_id][0] == 'Ticket':
                self._process_ticket(soup)

            elif self.incomings_xml[file_id][0] == 'FORM2REGINFO':
                self._process_regform2(soup)
        except ParsingError as _ex:
            logger.error(_ex)
            result = False
            writing_file_an_err(
                self.outgoing_xml,
                f'Error incoming parsing shipments {self.incomings_xml[file_id][0]}')

        self.incomings_xml[file_id][1] = ''
        return result

    def _get_client(self, soup: BeautifulSoup) -> None:
        consignee = soup.find('wb:Consignee')
        if consignee is None:
            raise ParsingError('Неизвестный тип xml shipments')

        try:
            self.client['name'] = self._get_value_from_tag(consignee, 'oref:FullName')
            self.client['fsrar_id'] = int(self._get_value_from_tag(consignee, 'oref:ClientRegId'))
            self.client['address'] = self._get_value_from_tag(consignee, 'oref:description')
        except ParsingError as _ex:
            raise ParsingError from _ex

        try:
            self.client['INN'] = consignee.find('oref:INN').text  # type: ignore
            self.client['KPP'] = consignee.find('oref:KPP').text  # type: ignore
        except AttributeError:
            pass

    def _get_footing(self, soup: BeautifulSoup) -> None:
        header = soup.find('Header')
        if header is not None:
            try:
                self.footing = self._get_value_from_tag(header, 'wb:Base')
                return None
            except ParsingError:
                pass
        self.footing = None

    def _get_transport_section(self, soup: BeautifulSoup) -> None:
        transport_section = soup.find('wb:Transport')
        if transport_section is None:
            raise ParsingError('Секция транспорта не найдена')
        try:
            self.transport = TransportShipments({
                'change_ownership': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:ChangeOwnership'),
                'train_company': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRAN_COMPANY'),
                'transport_number':  self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRANSPORT_REGNUMBER'),
                'train_trailer': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRAN_TRAILER'),
                'train_customer': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRAN_CUSTOMER'),
                'driver': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRAN_DRIVER'),
                'unload_point': self._get_value_from_tag(
                                                    transport_section,
                                                    'wb:TRAN_UNLOADPOINT')
            })
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _get_products(self, soup: BeautifulSoup) -> None:
        try:
            for row in soup.find_all('wb:Position'):
                identity = row.find('wb:Identity').text
                self.products[identity] = ProductShipments({
                        'alcocode': int(row.find('pref:AlcCode').text.rstrip()),
                        'name': row.find('pref:FullName').text.rstrip(),
                        'type_product': row.find('pref:Type').text.rstrip(),
                        'type_code': row.find('pref:ProductVCode').text.rstrip(),
                        'alcovolume': Decimal(row.find('pref:AlcVolume').text),
                        'quantity': Decimal(row.find('wb:Quantity').text),
                        'price': Decimal(row.find('wb:Price').text),
                        'form2_old': row.find('ce:F2RegId').text,
                        'form1': row.find('wb:FARegId').text,
                        'capacity': None,
                        'form2_new': None,
                        'bottling_date': None})

                try:
                    self.products[identity]['capacity'] = Decimal(row.find('Capacity').text)
                except AttributeError:
                    pass
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _process_ticket(self, soup: BeautifulSoup) -> None:
        try:
            operation_result = soup.find('tc:OperationResult').\
                find('tc:OperationResult').text  # type: ignore
        except AttributeError:
            operation_result = None

        if operation_result == 'Accepted':
            # If the file is 'Принято ЕГАИС', then we do not need to process the ticket
            if self.condition == 'Принято ЕГАИС':
                return

            self.condition = 'Принято ЕГАИС(без номера фиксации)'
        elif operation_result is None:
            pass
        else:
            self.condition = 'Отклонено ЕГАИС'
            signal('reject')

    def _process_regform2(self, soup: BeautifulSoup) -> None:
        try:
            self.fixation = FixationShipments({
                'ttn': self._get_value_from_tag(soup, 'wbr:WBRegId'),
                'fix_number': self._get_value_from_tag(soup, 'wbr:EGAISFixNumber'),
                'fix_date': datetime.strptime(
                                self._get_value_from_tag(soup, 'wbr:EGAISFixDate'),
                                '%Y-%m-%d').date()
            })
            self.condition = 'Принято ЕГАИС'

            for row in soup.find_all('wbr:Position'):
                ident = row.find('wbr:Identity').text
                self.products[ident]['form2_new'] = row.find('wbr:InformF2RegId').text
                self.products[ident]['bottling_date'] = datetime.strptime(
                                                            row.find('BottlingDate').text,
                                                            '%Y-%m-%d').date()
            signal('accept')
        except ParsingError as _ex:
            raise ParsingError from _ex

    def _load_from_file(self) -> None:
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')
        try:
            try:
                self.uuid = self._get_value_from_tag(soup, 'Identity')
                self.fixation['ttn'] = self._get_value_from_tag(soup, 'w1')
                self.fixation['fix_number'] = self._get_value_from_tag(soup, 'w2')
            except AttributeError:
                self.fixation['ttn'] = None
                self.fixation['fix_number'] = None

            for row in soup.find_all('wb:Position'):
                identity = row.find('wb:Identity').text
                self.products[identity]['form2_new'] = row.find('F2RegIdAssigned').text
                self.products[identity]['bottling_date'] = datetime.strptime(
                                                            '1970-01-01', '%Y-%m-%d').date()
        except ParsingError as _ex:
            raise ParsingError from _ex
    """
    ---------------------------------------------------------
    ------------------ WORK WITH DB -------------------------
    ---------------------------------------------------------
    """
    async def insert_shipment(self) -> bool:
        async with self.db.pool.acquire() as con:
            async with con.transaction():
                await self.check_client(self.client, con)

                self.id_in_base = await con.fetchval(
                                            query.insert_shipment_async,
                                            self.number,
                                            self.condition,
                                            self.uuid,
                                            self.date,
                                            self.client['fsrar_id'],
                                            self.footing)

                await con.execute(
                        query.insert_transport_async,
                        self.id_in_base,
                        self.transport['change_ownership'],
                        self.transport['train_company'],
                        self.transport['transport_number'],
                        self.transport['train_trailer'],
                        self.transport['train_customer'],
                        self.transport['driver'],
                        self.transport['unload_point'])

                for position, product in self.products.items():
                    await self.check_product(product, con)

                    await con.execute(
                        query.insert_cart_products_async,
                        self.id_in_base,
                        product['alcocode'],
                        position,
                        product['quantity'],
                        product['price'],
                        product['form2_old'],
                        product['form1'])
        return True

    async def update_shipment(self) -> bool:
        async with self.db.pool.acquire() as con:
            async with con.transaction():
                if self.condition == 'Принято ЕГАИС':
                    await con.execute(
                        query.update_shipment_regf2_async,
                        self.condition,
                        self.fixation['ttn'],
                        self.fixation['fix_number'],
                        self.id_in_base)

                    for position, product in self.products.items():
                        await con.execute(
                            query.update_cart_products_async,
                            product['form2_new'],
                            product['bottling_date'],
                            self.id_in_base,
                            position)

                elif self.condition in ['Принято ЕГАИС(без номера фиксации)', 'Отклонено ЕГАИС']:
                    await con.execute(query.update_shipment_cond_async,
                                      self.condition,
                                      self.id_in_base)

        logger.info(f"DB.update shipments: {self.condition}, {self.number}, id: {self.id_in_base}")
        return True


# legacy
@no_type_check
def parsing_acts(act: str) -> list:
    try:
        soup = BeautifulSoup(act, 'lxml-xml')
        try:
            date_act = datetime.strptime(soup.find('ActDate').text, '%Y-%m-%d').date()
            ttn_reg = soup.find('WBRegId').text
            is_accept = soup.find('IsAccept').text
        except AttributeError:
            ttn_reg = None
            is_accept = None
        positions = {}

        if is_accept == 'Accepted':
            state = 'Проведено'
        elif is_accept == 'Differences':
            state = 'Проведено частично'
            for position in soup.find_all('Position'):
                positions[position.find('InformF2RegId').text] = float(
                                            position.find('RealQuantity').text)
        else:
            state = 'Распроведено'
        return [state, ttn_reg, positions, date_act]
    except Exception:
        (act, 'from act')


# Thread method - legacy
@no_type_check
@logger.catch
def parsing_shipments(active_shipments, acts, db) -> None:  # noqa: C901
    while True:
        for uuid, ship in list(active_shipments.items()):
            if ship.outgoing_xml != '':
                try:
                    ship.parsing_outgoing_doc()
                except Exception:
                    writing_file_an_err(ship.outgoing_xml, 'from outgoing shipments')
                    ship.outgoing_xml = ''

                ship.id_in_base = db.insert_record_shipment(ship)

            # Checking that the shipment is not ready
            if ship.condition in ['Принято ЕГАИС', 'Отклонено ЕГАИС']:
                del active_shipments[uuid]
                continue

            for file_id in list(ship.incomings_xml.keys()):
                # Checking if the file is parsed
                if ship.incomings_xml[file_id][1] != '':
                    condition = ship.condition

                    try:
                        ship.parsing_incoming_doc(file_id)
                    except Exception:
                        writing_file_an_err(ship.incomings_xml[file_id][1],
                                            'from incoming shipments')
                        ship.incomings_xml[file_id][1] = ''

                    if ship.condition != condition:
                        db.update_record_shipment(ship)

        for row_id, act in list(acts.items()):
            # The act can hang in the queue for 20 minutes (5sec * 240)
            # In order not to constantly overwrite the row in the database,
            # we create a counter for the file, and after 20 minutes we delete it
            if type(act) is str:
                try:
                    state, ttn, positions, date_act = parsing_acts(act)
                    acts[row_id] = 0
                    db.update_record_waybill_act(state, ttn, positions, date_act)
                except Exception as err:
                    logger.error(f'Ошибка добавления БД акт: {err}')
                    del acts[row_id]
            else:
                acts[row_id] += 1
                if acts[row_id] > 240:
                    del acts[row_id]
        sleep(5)
