import asyncio
import psycopg2
import asyncpg

from app.configuration import get_conection_database, get_fsrar_id
from app.logs import logger
from app.services import error_parsing
from templates import query


class Database:
    def __init__(self, user, db_name=None) -> None:
        self.config_database: dict = get_conection_database(user)
        try:
            self.connection: psycopg2 = psycopg2.connect(host = self.config_database['host'],
                                    user = self.config_database['user'],
                                    password = self.config_database['password'],
                                    database = self.config_database['db_name'])
            self.connection.autocommit = True
            

        except Exception as _ex:
            logger.error(f'POSTGRES ERROR: {_ex}')

    def select_active_shipments(self) -> list:
        with self.connection.cursor() as cursor:
            cursor.execute(query.select_active_shipments)
            ships: list = [list(i) for i in cursor.fetchall()]

            for index, item in enumerate(ships):
                cursor.execute(query.select_cart_pr, (item[0],))
                ships[index].append(cursor.fetchall())
            return ships

    def select_sql(self, sql, item) -> list:
        with self.connection.cursor() as cursor:
             cursor.execute(sql, item)
             lst: list = cursor.fetchone()
        return lst
    
    def insert_or_update_sql(self, sql, data):
        with self.connection.cursor() as cursor:
             cursor.execute(sql, data)

    @logger.catch
    def check_client(self, client, cursor):
        if client['fsrar_id'] != None:
            cursor.execute(query.select_client, (client['fsrar_id'],))
            try:
                fsrar_id = cursor.fetchone()[0]
            except Exception:
                fsrar_id = None

            if fsrar_id == None:
                cursor.execute(query.insert_client, (client['name'], client['fsrar_id'], 
                                        client['INN'], client['KPP'], 
                                        client['address']))
    @logger.catch
    def check_product(self, product, cursor):
        try:
            cursor.execute(query.select_product, (product['alcocode'],))
            alcocode = cursor.fetchone()[0]
        except Exception:
            alcocode = None

        if alcocode == None: 
            own_fsrar_id = get_fsrar_id()
            if product['manufacturer']['fsrar_id'] == own_fsrar_id:
                is_own = True
            else: is_own = False

            cursor.execute(query.insert_product, (product['alcocode'], product['name'], 
                                    product['capacity'], product['alcovolume'], 
                                    product['type_product'], product['type_code'], 
                                    product['manufacturer']['fsrar_id'], is_own))

    @logger.catch
    def insert_record_shipment(self, ship) -> int:
        self.connection.autocommit = False
        with self.connection.cursor() as cursor:
            try:
                self.check_client(ship.client, cursor)
                    
                cursor.execute(query.insert_shipment, (ship.number, ship.condition, ship.uuid, 
                                    ship.date, ship.client['fsrar_id'], ship.footing))
                id_ship = cursor.fetchone()[0]
                
                cursor.execute(query.insert_transport, (id_ship, ship.transport['change_ownership'], ship.transport['train_company'], 
                                    ship.transport['transport_number'], ship.transport['train_trailer'], 
                                    ship.transport['train_customer'], ship.transport['driver'], 
                                    ship.transport['unload_point']))
                
                for position, product in ship.products.items():
                    self.check_product(product, cursor)

                    cursor.execute(query.insert_cart_products, (id_ship, product['alcocode'], position, 
                                        product['quantity'], product['price'], 
                                        product['form2_old'], product['form1']))
                
                self.connection.commit()
            except Exception:
                error_parsing('', 'error in insert db shipment')
                self.connection.rollback()
        self.connection.autocommit = True
        return id_ship

    @logger.catch
    def update_record_shipment(self, ship) -> None:
        with self.connection.cursor() as cursor:   
            # try:         
                if ship.condition == 'Принято ЕГАИС':
                    cursor.execute(query.update_shipment_regf2, (ship.condition, ship.fixation['ttn'], 
                                        ship.fixation['fix_number'],
                                        ship.id_in_base))
                    
                    for position, product in ship.products.items():
                        cursor.execute(query.update_cart_products, (product['form2_new'], 
                                        product['bottling_date'], ship.id_in_base, position))
                    
                elif ship.condition in  ['Принято ЕГАИС(без номера фиксации)', 'Отклонено ЕГАИС']:
                    cursor.execute(query.update_shipment_cond, (ship.condition, ship.id_in_base))
            # except Exception:
            #     error_parsing('', 'error in dp_update shipment')
            #     self.connection.rollback()
            #     return False
            
        logger.info(f"DB.update shipments: {ship.condition}, {ship.number}, id: {ship.id_in_base}")
        return True

    def update_record_waybill_act(self, condition, ttn, positions, date_act) -> None:
        with self.connection.cursor() as cursor:
            if condition == 'Проведено частично':
                for form2, position in positions.items():
                    cursor.execute(query.update_cart_product_partly, (position, form2))
            cursor.execute(query.update_shipment_partly, (condition, date_act, ttn))
            
        logger.info(f"DB.update act: {condition}, {ttn}, {date_act}, {positions}")


    def update_status_modules(self, module_name, states):
        times = 'now()'
        with self.connection.cursor() as cursor:
            if states:
                cursor.execute(query.update_status_modules, (states, times, None, module_name))
            else: 
                cursor.execute(query.update_status_modules.replace('time_start = %s,', ''), 
                              (states, times, module_name))


class Async_database:
    def __init__(self, user, loop=None) -> None:
        self.user = user
        self.config_database: dict = get_conection_database(self.user)

    async def get_connection(self):
        try:
            self.pool: asyncpg = await asyncpg.create_pool(
                                    host = self.config_database['host'],
                                    user = self.config_database['user'],
                                    password = self.config_database['password'],
                                    database = self.config_database['db_name'])
        except Exception as _ex:
            logger.error(f'async - POSTGRES ERROR: {_ex}')

    async def select_sql(self, sql, *args) -> asyncpg.Record:
        try:
            async with self.pool.acquire() as con:
                return await con.fetch(sql, *args)
        except asyncpg.exceptions.PostgresSyntaxError as _err:
            logger.error(f'async - POSTGRES_select_sql: {_err}')

    async def instert_sql(self, sql, *args):
        try:
            async with self.pool.acquire() as con:
                return await con.execute(sql, *args)
        except asyncpg.exceptions.PostgresSyntaxError as _err:
            logger.error(f'async - POSTGRES_insert_sql: {_err}')

    async def update_sql(self, sql, *args):
        try: 
            async with self.pool.acquire() as con:
                return await con.execute(sql, *args)
        except asyncpg.exceptions.PostgresSyntaxError as _err:
            logger.error(f'BOT - POSTGRES_upd_sql: {_err}')

    async def listen_db(self, listener) -> asyncpg.Record:
        self.conn: asyncpg = await asyncpg.connect(
                                    host = self.config_database['host'],
                                    user = self.config_database['user'],
                                    password = self.config_database['password'],
                                    database = self.config_database['db_name'])
        await self.conn.add_listener('ships_insert_or_update', listener)
        await self.conn.add_listener('tr_insert', listener)
    