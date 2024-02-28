import asyncio
from decimal import Decimal
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup

from base.database import Async_database
from app.services import signal, error_parsing, Doc_utm
from app.settings import db
from app.logs import logger
from templates import query


class Shipment(Doc_utm):
    def parsing_outgoing_doc(self) -> None:
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')

        self.number = int(soup.find('wb:NUMBER').text)
        self.date = datetime.strptime(soup.find('wb:Date').text, '%Y-%m-%d').date()
        self.client = {'name': soup.find('wb:Consignee').find('oref:FullName').text.replace("'", "''"), 
                    'fsrar_id': int(soup.find('wb:Consignee').find('oref:ClientRegId').text),
                    'address': soup.find('wb:Consignee').find('oref:description').text.replace("'", "''")}
        
        try:
            self.client['INN'] = soup.find('wb:Consignee').find('oref:INN').text
            self.client['KPP'] =  soup.find('wb:Consignee').find('oref:KPP').text
        except AttributeError:
            self.client['INN'] = None
            self.client['KPP'] = None
        try:
            self.footing = soup.find('wb:Header').find('wb:Base').text 
        except AttributeError:  
            self.footing = None

        for rows in soup.find_all('wb:Transport'):
            self.transport['change_ownership'] = rows.find('wb:ChangeOwnership').text
            self.transport['train_company'] = rows.find('wb:TRAN_COMPANY').text.replace("'", "''")
            self.transport['transport_number'] = rows.find('wb:TRANSPORT_REGNUMBER').text
            self.transport['train_trailer'] = rows.find('wb:TRAN_TRAILER').text
            self.transport['train_customer'] = rows.find('wb:TRAN_CUSTOMER').text.replace("'", "''")
            self.transport['driver'] = rows.find('wb:TRAN_DRIVER').text
            self.transport['unload_point'] = rows.find('wb:TRAN_UNLOADPOINT').text.replace("'", "''")

        
        for rows in soup.find_all('wb:Position'):
            self.products[rows.find('wb:Identity').text] = {'alcocode': int(rows.find('pref:AlcCode').text.rstrip()),
                                                            'name': rows.find('pref:FullName').text.rstrip().replace("'", "''"),
                                                            'type_product': rows.find('pref:Type').text.rstrip(),
                                                            'type_code': rows.find('pref:ProductVCode').text.rstrip(),
                                                            'alcovolume': Decimal(rows.find('pref:AlcVolume').text),
                                                            'quantity': int(rows.find('wb:Quantity').text.split('.')[0]),
                                                            'price': Decimal(rows.find('wb:Price').text),
                                                            'form2_old': rows.find('ce:F2RegId').text,
                                                            'form1': rows.find('wb:FARegId').text}
            
            try:
                self.products[rows.find('wb:Identity').text]['capacity'] = Decimal(rows.find('Capacity').text)
            except AttributeError:
                self.products[rows.find('wb:Identity').text]['capacity'] = None

            if self.uuid == 'repeat':
                self.products[rows.find('wb:Identity').text]['form2_new'] = rows.find('F2RegIdAssigned').text
                self.products[rows.find('wb:Identity').text]['bottling_date'] = datetime.strptime('1970-01-01', '%Y-%m-%d').date()
        
        #to add manually from tools 'load_data_from_xml' 
        if self.uuid == 'repeat':
            try:
                self.uuid = soup.find('Identity').text
                self.fixation['ttn'] = soup.find('w1').text
                self.fixation['fix_number'] = soup.find('w2').text

            except AttributeError:
                self.fixation['ttn'] = None
                self.fixation['fix_number'] = None

        self.outgoing_xml = ''


    def parsing_incoming_doc(self, file_id) -> None:
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        # There are two types of response files: Ticket and FORM2REGINFO
        # Tickets are a response from the server and a local check
        # tc:OperationResult - response from the server
        # tc:Conclusion - local check
        if self.incomings_xml[file_id][0] == 'Ticket': 
            try: 
                operation_result = soup.find('tc:OperationResult').find('tc:OperationResult').text
            except AttributeError:
                operation_result = None
                    
            if operation_result == 'Accepted' :
                #If the file is 'Принято ЕГАИС', then we do not need to process the ticket
                if self.condition == 'Принято ЕГАИС': 
                    self.incomings_xml[file_id][1] = ''
                    return

                self.condition = 'Принято ЕГАИС(без номера фиксации)'
            elif operation_result == None: pass
            else:
                self.condition = 'Отклонено ЕГАИС'
                signal('reject')
                
        elif self.incomings_xml[file_id][0] == 'FORM2REGINFO':
            self.fixation['ttn'] = soup.find('wbr:WBRegId').text
            self.fixation['fix_number'] = soup.find('wbr:EGAISFixNumber').text
            self.fixation['fix_date'] = datetime.strptime(soup.find('wbr:EGAISFixDate').text, '%Y-%m-%d').date()
            self.condition = 'Принято ЕГАИС'

            for row in soup.find_all('wbr:Position'):
                self.products[row.find('wbr:Identity').text]['form2_new'] = row.find('wbr:InformF2RegId').text
                self.products[row.find('wbr:Identity').text]['bottling_date'] = datetime.strptime(
                                                                    row.find('BottlingDate').text, 
                                                                    '%Y-%m-%d').date()
            signal('accept')
            
        self.incomings_xml[file_id][1] = ''
            
#legacy            
def get_active_shipments() -> None:
    active_shipments: dict = {}
    response = db.select_active_shipments()
    if len(response) == 0: return {}
    for ship in response:
                    #active_shipments[keys] = Object Shipment
        active_shipments[ship[2]] = Shipment(ship[2], '', ship[1])
        active_shipments[ship[2]].id_in_base = ship[0]
        active_shipments[ship[2]].number = ship[3]
        for product in ship[4]:
            active_shipments[ship[2]].products[product[0]] = {'form2_old': product[1]}
    return active_shipments

#legacy       
def parsing_acts(act) -> list:
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
                positions[position.find('InformF2RegId').text] = float(position.find('RealQuantity').text)
        else: state = 'Распроведено'
        return [state, ttn_reg, positions, date_act]
    except Exception:
        error_parsing(act, 'from act')

# Thread method - legacy
@logger.catch
def parsing_shipments(active_shipments, acts, db) -> None:
    while True:
        for uuid, ship in list(active_shipments.items()):
            if ship.outgoing_xml != '':
                try:     
                    ship.parsing_outgoing_doc()
                except Exception:
                    error_parsing(ship.outgoing_xml, 'from outgoing shipments')
                    ship.outgoing_xml = ''

                ship.id_in_base = db.insert_record_shipment(ship)
                
            #Checking that the shipment is not ready
            if ship.condition in ['Принято ЕГАИС', 'Отклонено ЕГАИС']:
                del active_shipments[uuid]
                continue

            for file_id in list(ship.incomings_xml.keys()):
                #Checking if the file is parsed
                if ship.incomings_xml[file_id][1] != '': 
                    condition = ship.condition
                    
                    try:
                        ship.parsing_incoming_doc(file_id)
                    except Exception:
                        error_parsing(ship.incomings_xml[file_id][1], 'from incoming shipments')
                        ship.incomings_xml[file_id][1] = ''

                    if ship.condition != condition: 
                        db.update_record_shipment(ship)

        for row_id, act in list(acts.items()):
            # The act can hang in the queue for 20 minutes (5sec * 240)
            # In order not to constantly overwrite the row in the database, 
            # we create a counter for the file, and after 20 minutes we delete it
            if type(act) == str:
                try:
                    state, ttn, positions, date_act = parsing_acts(act)
                    acts[row_id] = 0
                    db.update_record_waybill_act(state, ttn, positions, date_act)
                except Exception as err:
                    logger.error(f'Ошибка добавления БД акт: {err}')
                    del acts[row_id]
            else: 
                acts[row_id] += 1
                if acts[row_id] > 240: del acts[row_id]
        sleep(5)



"""
---------------------------------------------------------------------------------------------------
------------------------------------------ HANDLER SHIPMENTS DOCS ----------------------------------------
---------------------------------------------------------------------------------------------------
"""
# aio + rabbitmq parsing
# The processing functions return a tuple of the form: 
# (Whether successfully processed; if so, the processed object)
class Handler_ships_docs:
    def __init__(self, db) -> None:
        self.db = db
        self.active_ships: dict = {}
    

    async def get_active_shipments(self) -> None:
        active_shipments: dict = {}
        async with self.db.pool.acquire() as con: 
            rows = [i for i in await con.fetch(query.select_active_shipments)]
            for item in rows:
                active_shipments[str(item['uuid'])] = Shipment(str(item['uuid']), '', item['condition'])
                active_shipments[str(item['uuid'])].id_in_base = item['id']
                active_shipments[str(item['uuid'])].number = item['num']
                response = await con.fetch(query.select_cart_pr_async, item['id'])
                for product in response:
                    active_shipments[str(item['uuid'])].products[
                                            product['positions']] = {'form2_old': product['form2_old']}                      
        self.active_ships = active_shipments
        return self.active_ships   

    def parsing_acts(self, act) -> list:
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
                    positions[position.find('InformF2RegId').text] = float(position.find('RealQuantity').text)
            else: state = 'Распроведено'
            return [state, ttn_reg, positions, date_act]
        except Exception:
            error_parsing(act, 'from act')

    """
    ---------------------------------------------------------------------------------------------------
    ------------------------------------------ WORK WITH DB -------------------------------------------
    ---------------------------------------------------------------------------------------------------
    """

    async def insert_shipment(self, ship) -> int:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr:  
                await ship.check_client(ship.client, con)
                    
                ship.id_in_base = await con.fetchval(query.insert_shipment_async, ship.number, ship.condition, 
                                                ship.uuid, ship.date, ship.client['fsrar_id'], ship.footing)
                                
                await con.execute(query.insert_transport_async, ship.id_in_base, ship.transport['change_ownership'], 
                                    ship.transport['train_company'], 
                                    ship.transport['transport_number'], ship.transport['train_trailer'], 
                                    ship.transport['train_customer'], ship.transport['driver'], 
                                    ship.transport['unload_point'])
                
                for position, product in ship.products.items():
                    await ship.check_product(product, con)

                    await con.execute(query.insert_cart_products_async, ship.id_in_base, product['alcocode'], position, 
                                        product['quantity'], product['price'], 
                                        product['form2_old'], product['form1'])
        return True

    async def update_shipment(self, ship) -> None:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr:        
                if ship.condition == 'Принято ЕГАИС':
                    await con.execute(query.update_shipment_regf2_async, ship.condition, ship.fixation['ttn'], 
                                        ship.fixation['fix_number'], ship.id_in_base)
                    
                    for position, product in ship.products.items():
                        await con.execute(query.update_cart_products_async, product['form2_new'], 
                                        product['bottling_date'], ship.id_in_base, position)
                    
                elif ship.condition in  ['Принято ЕГАИС(без номера фиксации)', 'Отклонено ЕГАИС']:
                    await con.execute(query.update_shipment_cond_async, ship.condition, ship.id_in_base)
            
        logger.info(f"DB.update shipments: {ship.condition}, {ship.number}, id: {ship.id_in_base}")

    async def update_waybill_act(self, condition, ttn, positions, date_act) -> None:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr:    
                if condition == 'Проведено частично':
                    for form2, position in positions.items():
                        await con.execute(query.update_cart_product_partly_async, position, form2)
                await con.execute(query.update_shipment_partly_async, condition, date_act, ttn)
        logger.info(f"DB.update act: {condition}, {ttn}, {date_act}, {positions}")

    """
    ---------------------------------------------------------------------------------------------------
    ------------------------------------------ PROCESSING ---------------------------------------------
    ---------------------------------------------------------------------------------------------------
    """

    async def processing_out_shipments(self, msg) -> bool:
        if msg['uuid'] not in self.active_ships.keys():
            self.active_ships[msg['uuid']] = Shipment(msg['uuid'], msg['xml'])
            shipment = self.active_ships[msg['uuid']]
            shipment.parsing_outgoing_doc()

            result = await self.insert_shipment(shipment)
            if result: return True
            return False

    async def processing_in_shipments(self, msg, rbmq) -> bool:
            if msg['type_file'] in ['FORM2REGINFO', 'Ticket']:
                try:
                    ship = self.active_ships[msg['uuid']]
                except KeyError:
                    if msg['type_file'] == 'Ticket':
                        return True
                    logger.error('KeyError in ships')
                    return False
                ship.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]
                
                #Checking if the file is parsed
                if ship.incomings_xml[msg['id_doc']][1] != '': 
                    condition = ship.condition    
                    ship.parsing_incoming_doc(msg['id_doc'])
                    
                    if ship.condition != condition: 
                        await self.update_shipment(ship) 
                    
                    if self.active_ships[msg['uuid']].condition in ['Принято ЕГАИС', 'Отклонено ЕГАИС']:
                            await rbmq.publication_task_json({'type_file': msg['type_file'], 
                                            'uuid': msg['uuid'], 
                                            'id_doc': msg['id_doc']}, 'active-queue', False) 
                            del self.active_ships[msg['uuid']]
            
            elif msg['type_file'] == 'WayBillAct_v4':
                act = msg['xml']
                state, ttn, positions, date_act = parsing_acts(act)
                await self.update_waybill_act(state, ttn, positions, date_act)
                await rbmq.publication_task_json({'type_file': msg['type_file'], 
                                        'uuid': msg['uuid'], 
                                        'id_doc': msg['id_doc']}, 'active-queue', False) 
            else:
                error_parsing(msg['xml'], 'Неопознанный тип файла в ships')
                return False 
            
            return True