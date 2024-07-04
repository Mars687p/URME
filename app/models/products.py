from decimal import Decimal
from typing import Any, Dict

from bs4 import BeautifulSoup

from app.logs import logger
from app.models.base_models import DocUtm
from base.database import Async_database
from custom_types.counterparty import Counterparty
from custom_types.products import ProductReference


class Product(DocUtm):
    def __init__(self, uuid: str,
                 outgoing_xml: str,
                 db: Async_database) -> None:
        super().__init__(uuid, outgoing_xml, db)
        self.products: Dict[int, ProductReference] = {}

    def parsing_outgoing_doc(self) -> None:
        pass

    def parsing_incoming_doc(self, file_id: int) -> None:
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        if 'ReplyAP' not in self.incomings_xml[file_id][0]:
            self.incomings_xml[file_id][1] = ''
            return None

        for index, row in enumerate(soup.find_all('Product')):
            if row.find('Producer') is None:
                continue
            result = self._format_products(index, row)
            if not result:
                logger.warning(f'Не удалось обработать продукт. \n{row}')
                continue
            result = self._format_manufacturer(index, row)
            if not result:
                logger.warning(f'Не удалось обработать производителя. \n{row}')
                continue

        self.incomings_xml[file_id][1] = ''

    def _format_products(self, index: int, row: Any) -> bool:
        self.products[index] = ProductReference({
            'alcocode': int(row.find('AlcCode').text.rstrip()),
            'name': row.find('FullName').text.rstrip().replace("'", "''"),
            'type_code': int(row.find('ProductVCode').text.rstrip()),
            'alcovolume': Decimal(row.find('AlcVolume').text),
            'type_product': '',
            'capacity': None,
            'manufacturer': Counterparty({
                                'fsrar_id': None,
                                'name': None,
                                'address': None,
                                'INN': None,
                                'KPP': None})
            })

        try:
            self.products[index]['type_product'] = row.find('Type').text.rstrip()
        except AttributeError:
            self.products[index]['type_product'] = 'АП'
        try:
            self.products[index]['capacity'] = Decimal(row.find('Capacity').text)
        except AttributeError:
            self.products[index]['capacity'] = None
        return True

    def _format_manufacturer(self, index: int, row: Any) -> bool:
        try:
            producer = row.find('Producer')
            mnaufacturer = self.products[index]['manufacturer']
            mnaufacturer['fsrar_id'] = int(producer.find('ClientRegId').text.rstrip())
            mnaufacturer['name'] = producer.find('FullName').text.rstrip().replace("'", "''")
            mnaufacturer['address'] = producer.find('description').text

        except AttributeError:
            mnaufacturer = Counterparty({
                                    'fsrar_id': None,
                                    'name': None,
                                    'address': None,
                                    'INN': None,
                                    'KPP': None})

        try:
            mnaufacturer['INN'] = \
                int(row.find('wb:Consignee').find('oref:INN').text)
            mnaufacturer['KPP'] = \
                int(row.find('wb:Consignee').find('oref:KPP').text)
        except AttributeError:
            pass
        return True

    async def insert_db(self) -> bool:
        async with self.db.pool.acquire() as con:
            async with con.transaction():
                for index in self.products.keys():
                    await self.check_client(self.products[index]['manufacturer'],
                                            con)
                    await self.check_product(self.products[index], con)

        logger.info('Обновление справочников продукции.')
        return True
