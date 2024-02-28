import asyncio
from decimal import Decimal
from datetime import datetime
from bs4 import BeautifulSoup

from app.services import Doc_utm
from app.logs import logger
from app.services import signal, error_parsing
from templates import query



class Manufacture(Doc_utm):    
    def parsing_outgoing_doc(self):
        soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')

        self.number = soup.find('NUMBER').text
        self.date = datetime.strptime(soup.find('Date').text, '%Y-%m-%d').date()
        self.date_production = datetime.strptime(soup.find('ProducedDate').text, '%Y-%m-%d').date()
        self.type_operation = soup.find('rpp:Type').text

        try:
            self.footing = soup.find('Header').find('Note').text 
        except AttributeError:  
            self.footing = None
            
        for rows in soup.find_all('Position'):
            identity = int(rows.find('Identity').text)
            self.products[identity] = {'alcocode': int(rows.find('ProductCode').text.rstrip()),
                                        'alcovolume': Decimal(rows.find('alcPercent').text),
                                        'quantity': Decimal(rows.find('Quantity').text),
                                        'party': rows.find('Party').text,}
            self.products[identity]['raw'] = {}
            for item in rows.find_all('Resource'):
                # A dictionary of products with a position key. 
                # Includes a dictionary of raw materials with keys for the position of this raw material
                # products[keys_position][raw][raws_position] = {dict raw_product}
                self.products[identity]['raw'][int(item.find('IdentityRes').text)] = \
                                        {'alcocode': int(item.find('AlcCode').text.rstrip()),
                                        'form2': item.find('RegForm2').text,
                                        'quantity': Decimal(item.find('Quantity').text),
                                        'alcovolume': Decimal(item.find('AlcVolume').text),}
        self.outgoing_xml = None

    def parsing_incoming_doc(self, file_id):
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        # There are two types of response files: Ticket and FORM1REGINFO
        # Tickets are a response from the server and a local check
        # OperationResult - response from the server
        # Conclusion - local check
        if self.incomings_xml[file_id][0] == 'Ticket': 
            try: 
                operation_result = soup.find('OperationResult').find('OperationResult').text
            except AttributeError:
                operation_result = None


            if operation_result == 'Accepted':
                    self.fixation['RegID'] = soup.find('RegID').text
                    self.fixation['fix_date'] = datetime.strptime(soup.find('OperationDate').text, '%Y-%m-%dT%H:%M:%S.%f').date()
                    if self.condition != 'Зафиксировано в ЕГАИС':
                        self.condition = 'Принято ЕГАИС'
           
            elif operation_result == None: 
                operation_result = soup.find('Conclusion').text
                if operation_result == 'Accepted':
                    return
                else: 
                    self.condition = 'Отклонено ЕГАИС'
                    signal('reject')      
            else:
                self.condition = 'Отклонено ЕГАИС'
                signal('reject')
                
        elif self.incomings_xml[file_id][0] == 'FORM1REGINFO':
            for row in soup.find_all('wbr:Position'):
                self.products[int(row.find('wbr:Identity').text)] = {'form1': row.find('wbr:InformF1RegId').text,
                                                                    'form2': row.find('wbr:InformF2RegId').text}
            self.condition = 'Зафиксировано в ЕГАИС'
        
        self.incomings_xml[file_id][1] = ''



"""
---------------------------------------------------------------------------------------------------
------------------------------------------ HANDLER MANUFACTURES DOCS ----------------------------------------
---------------------------------------------------------------------------------------------------
"""

class Handler_mf_docs:
    def __init__(self, db) -> None:
        self.db = db
        self.active_mf: dict = {}

    async def get_active_mf(self) -> dict:
        mf: dict = {}
        async with self.db.pool.acquire() as con: 
            rows = [i for i in await con.fetch(query.select_active_mf)]
            for item in rows:
                #active_mf[keys] = Object mf
                mf[str(item['uuid'])] = Manufacture(str(item['uuid']), '', item['condition'])
                mf[str(item['uuid'])].id_in_base = item['id']
                response = await con.fetch(query.select_mf_product_async, item['id'])
                for product in response:
                    mf[str(item['uuid'])].products[product['positions']] = {}                      
        self.active_mf = mf
        return self.active_mf

    def parsing_mf_acts(self, act) -> list:
        try:
            soup = BeautifulSoup(act, 'lxml-xml')
            try:
                date_act = datetime.strptime(soup.find('TicketDate').text, '%Y-%m-%d').date()
                reg_id = soup.find('RegId').text
                is_accept = soup.find('OperationResult').text
            except AttributeError:
                reg_id = None
                is_accept = None     
            positions = {}

            if is_accept == 'Accepted': 
                state = 'Распроведено'
                return [state, reg_id, positions, date_act]
            else:
                error_parsing(act, 'from act mf: Неизвестный формат')
        except Exception:
            error_parsing(act, 'from act')

    def parsing_mf_wbf_num(self, doc):
        try:
            soup = BeautifulSoup(doc, 'lxml-xml')
            date_mf = datetime.strptime(soup.find('OriginalDocDate').text, '%Y-%m-%d').date()
            num_mf = soup.find('OriginalDocNumber').text
            wbf_num = soup.find('EGAISNumber').text
            return (wbf_num, date_mf, num_mf)
        except Exception:
            error_parsing(doc, 'from act')

    """
    ---------------------------------------------------------------------------------------------------
    ------------------------------------------ WORK WITH DB -------------------------------------------
    ---------------------------------------------------------------------------------------------------
    """
    async def insert_db(self, mf) -> bool:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr:       
                mf.id_in_base = await con.fetchval(query.insert_record_manufactures, mf.number, mf.condition, mf.uuid, 
                                                    mf.date, mf.date_production, mf.type_operation,  
                                                    mf.footing)
                
                for position, product in mf.products.items():
                    try:
                        alcocode =await con.fetchval(query.select_product_async, product['alcocode'])
                    except TypeError:
                        logger.error(f'Продукта {product["alcocode"]} нет в справочнике продукции')
                        return
                    
                    # mfed product
                    pr_id = await con.fetchval(query.insert_manufactured_pr, mf.id_in_base, alcocode, position, 
                                        product['quantity'], product['party'], product['alcovolume'])
                    
                    # raw
                    for pos in product['raw'].keys():
                        raw = product['raw'][pos]
                        try:
                            alcocode = await con.fetchval(query.select_product_async, raw['alcocode'])
                        except Exception as _ex:
                            logger.error(f'Продукта {raw["alcocode"]} нет в справочнике продукции. {_ex}')
                            await tr.rollback()
                            return False
                    
                        await con.execute(query.insert_raw_pr, pr_id, alcocode, pos, 
                                        raw['quantity'], raw['form2'])

        return True
    
    async def update_mf(self, mf) -> bool:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr: 
                if mf.condition == 'Зафиксировано в ЕГАИС':
                    await con.execute(query.update_mf_cond, mf.condition,
                                                        mf.id_in_base)
                    for position, product in mf.products.items():
                        await con.execute(query.update__mfed_products, product['form1'], 
                                        product['form2'], mf.id_in_base, position)
            
                elif mf.condition == 'Отклонено ЕГАИС':
                    await con.execute(query.update_mf_cond, mf.condition, mf.id_in_base)

                if mf.fixation != {}:
                    await con.execute(query.update__mf_regdata, mf.fixation['RegID'], 
                            mf.fixation['fix_date'], mf.id_in_base)
                    if mf.condition == 'Принято ЕГАИС':
                        await con.execute(query.update_mf_cond, mf.condition, mf.id_in_base)

        logger.info(f"DB.update manufactures: {mf.condition}, {mf.number}, id: {mf.id_in_base}")   
        return True    

    async def update_db_mf_acts(self, state, reg_id, positions, date_act):
        async with self.db.pool.acquire() as con: 
            await con.execute(query.update_mf_act, state, date_act, reg_id)
        logger.info(f"DB.update mf act: {state}, {reg_id}, {date_act}, {positions}") 
        return True



    """
    ---------------------------------------------------------------------------------------------------
    ------------------------------------------ PROCESSING ---------------------------------------------
    ---------------------------------------------------------------------------------------------------
    """

    async def processing_out_mf(self, msg) -> bool:
        result = False
        if msg['uuid'] not in self.active_mf.keys():
            self.active_mf[msg['uuid']] = Manufacture(msg['uuid'], msg['xml'])
            mf = self.active_mf[msg['uuid']]  
            mf.parsing_outgoing_doc()
            result = await self.insert_db(mf)
            
            if result: return True
            return False

    async def processing_in_mf(self, msg, rbmq) -> bool:
        result = False
        if msg['type_file'] in ['FORM1REGINFO', 'Ticket']:
            try:
                mf = self.active_mf[msg['uuid']]
            except KeyError:
                if msg['type_file'] == 'Ticket':
                    return True
                else: return False
            mf.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]
            
            #Checking if the file is parsed
            if mf.incomings_xml[msg['id_doc']][1] != '': 
                try:     
                    mf.parsing_incoming_doc(msg['id_doc'])
                    result = await self.update_mf(mf) 
                except Exception:
                    error_parsing(msg['xml'], 'from incoming mf')
                    return False
                                
                if (self.active_mf[msg['uuid']].fixation != {} and
                self.active_mf[msg['uuid']].condition == 'Зафиксировано в ЕГАИС') or \
                self.active_mf[msg['uuid']].condition == 'Отклонено ЕГАИС':
                    await rbmq.publication_task_json({'type_file': msg['type_file'], 
                                    'uuid': msg['uuid'], 
                                    'id_doc': msg['id_doc']}, 'active-queue', False) 
                    del self.active_mf[msg['uuid']]
                
                return True

        elif msg['type_file'] == 'QueryRejectRepProduced':
            act = msg['xml']
            state, reg_id, positions, date_act = self.parsing_mf_acts(act)
            result = await self.update_db_mf_acts(state, reg_id, positions, date_act)
            await rbmq.publication_task_json({'type_file': msg['type_file'], 
                                'uuid': msg['uuid'], 
                                'id_doc': msg['id_doc']}, 'active-queue', False) 
            if not result: 
                logger.error('Ошибка добавления БД: mf act')
            return result
        
        elif msg['type_file'] == 'ReplyForm1':
            doc = msg['xml']
            try:
                data = self.parsing_mf_wbf_num(doc)
                await self.db.update_sql(query.update_mf_wbf_num, *data)
                await rbmq.publication_task_json({'type_file': msg['type_file'], 
                                'uuid': msg['uuid'], 
                                'id_doc': msg['id_doc']}, 'active-queue', False) 
                return True
            except Exception as err:
                logger.error(f'Ошибка добавления БД wbf: {err}')
                error_parsing(msg['xml'], 'Ошибка добавления БД wbf mf')
            
        if result: return True    
        return False
