from abc import ABC
from typing import Any, Dict, Optional, Union

import asyncpg
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from app.configuration import get_fsrar_id
from app.logs import logger
from base.database import Async_database
from custom_types.counterparty import Counterparty
from custom_types.products import ProductReference, ProductShipments
from exeptions.parsing_error import ParsingError
from templates import query


class Entity(ABC):
    def __init__(self,
                 uuid: str,
                 db: Async_database,
                 outgoing_xml: str = '') -> None:
        self.uuid = uuid
        self.db = db
        self.outgoing_xml = outgoing_xml
        self.incomings_xml: Dict[int, list[str]] = {}

    def _get_value_from_tag(self,
                            soup: Union[BeautifulSoup, Tag, NavigableString],
                            tag_name: str) -> str:
        tag: Tag = soup.find(tag_name)  # type: ignore
        if tag is None:
            raise ParsingError(f'{tag_name} не найден')
        return tag.text


class DocUtm(Entity):

    def __init__(self,
                 uuid: str,
                 outgoing_xml: str,
                 db: Async_database,
                 condition: str = 'Отправлено') -> None:
        super().__init__(uuid, db, outgoing_xml)
        self.condition: str = condition
        self.number: Union[str, int] = ''
        self.products: Any = {}
        self.fixation: Any = {}
        self.footing: Optional[str] = None
        self.db: Async_database = db
        self.id_in_base = None

    @logger.catch
    async def check_client(self,
                           client: Counterparty,
                           con: asyncpg.pool.PoolConnectionProxy) -> None:
        if client['fsrar_id'] is not None:
            fsrar_id = await con.fetchrow(query.select_client_async,
                                          client['fsrar_id'])
            if fsrar_id is None:
                await con.execute(
                                query.insert_client_async,
                                client['name'], client['fsrar_id'],
                                client['INN'],
                                client['KPP'],
                                client['address'])
            else:
                if fsrar_id.get('adress') != client['address']:
                    await con.execute(query.update_client_async,
                                      client['address'],
                                      client['fsrar_id'])

    @logger.catch
    async def check_product(self,
                            product: Union[ProductReference, ProductShipments],
                            con: asyncpg.pool.PoolConnectionProxy) -> None:
        alcocode = await con.fetchval(query.select_product_async, product['alcocode'])
        if alcocode is None:
            own_fsrar_id = get_fsrar_id()
            if product.get('manufacturer') is None:
                await con.execute(
                            query.insert_product_async,
                            product['alcocode'],
                            product['name'],
                            product['capacity'],
                            product['alcovolume'],
                            product['type_product'],
                            product['type_code'],
                            None,
                            False)
                logger.warning(f"Производитель продукта({product['alcocode']}) неизвестен")
                return

            fsrar_id: int = product['manufacturer']['fsrar_id']  # type: ignore
            if fsrar_id == own_fsrar_id:
                is_own = True
            else:
                is_own = False
            await con.execute(
                            query.insert_product_async,
                            product['alcocode'],
                            product['name'],
                            product['capacity'],
                            product['alcovolume'],
                            product['type_product'],
                            product['type_code'],
                            fsrar_id,
                            is_own)


class ActUtm(Entity):
    def __init__(self,
                 uuid: str,
                 db: Async_database,
                 outgoing_xml: str = '',
                 incoming_xml: str = '') -> None:
        super().__init__(uuid, db, outgoing_xml)
        self.incoming_xml = incoming_xml
