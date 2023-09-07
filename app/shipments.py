from datetime import datetime
from time import sleep

from bs4 import BeautifulSoup
from pygame import mixer
from app.configuration import get_file_path
from app.logs import logger



class Shipment:
    def __init__(self, uuid, outgoing_xml, condition='Отправлено') -> None:
        self.outgoing_xml = outgoing_xml
        self.uuid = uuid
        self.incomings_xml: dict = {}
        self.condition: str = condition
        self.number: str = ''
        self.client: dict = {}
        self.transport: dict = {}
        self.products: dict = {}
        self.fixation: dict = {}
        self.id_in_base = 0


    def parsing_outgoing_doc(self) -> None:
        try:
            soup = BeautifulSoup(self.outgoing_xml, 'lxml-xml')

            self.number = soup.find('wb:NUMBER').text
            self.date = datetime.strptime(soup.find('wb:Date').text, '%Y-%m-%d').date()
            self.client = {'name': soup.find('wb:Consignee').find('oref:FullName').text.replace("'", "''"), 
                        'fsrar_id': int(soup.find('wb:Consignee').find('oref:ClientRegId').text),
                        'address': soup.find('wb:Consignee').find('oref:description').text.replace("'", "''")}
            
            try:
                self.client['INN'] = soup.find('wb:Consignee').find('oref:INN').text
                self.client['KPP'] =  soup.find('wb:Consignee').find('oref:KPP').text
            except AttributeError:
                self.client['INN'] = '-'
                self.client['KPP'] = '-'

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
                                                                'capacity': float(rows.find('pref:Capacity').text),
                                                                'alcovolume': float(rows.find('pref:AlcVolume').text),
                                                                'quantity': int(rows.find('wb:Quantity').text.split('.')[0]),
                                                                'price': float(rows.find('wb:Price').text),
                                                                'form2_old': rows.find('ce:F2RegId').text,
                                                                'form1': rows.find('wb:FARegId').text}
                if self.uuid == 'repeat':
                    self.products[rows.find('wb:Identity').text]['form2_new'] = rows.find('F2RegIdAssigned').text
                    self.products[rows.find('wb:Identity').text]['bottling_date'] = datetime.strptime('1970-01-01', '%Y-%m-%d').date()
            
            if self.uuid == 'repeat':
                self.fixation['ttn'] = soup.find('w1').text
                self.fixation['fix_number'] = soup.find('w2').text
                self.uuid = soup.find('Identity').text
        except Exception as err:
            error_parsing(self.outgoing_xml, 'from outgoing xml', err)
        self.outgoing_xml = ''


    def parsing_incoming_doc(self, file_id) -> None:
        try:
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
            
        except Exception as err:
            error_parsing(self.incomings_xml[file_id][1], 'from incoming xml', err)
        
        self.incomings_xml[file_id][1] = ''
            


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
            for position in soup.find('Position').text:
                positions[position.find('InformF2RegId').text] = float(position.find('RealQuantity').text)
        else: state = 'Распроведено'
        return [state, ttn_reg, positions, date_act]
    except Exception as err:
        error_parsing(act, 'from act', err)

@logger.catch
def parsing_shipments(active_shipments, acts, db) -> None:
    while True:
        for uuid, ship in list(active_shipments.items()):
            if ship.outgoing_xml != '': 
                ship.parsing_outgoing_doc()
                ship.id_in_base = db.insert_record_shipment(ship)
                
            #Checking that the shipment is not ready
            if ship.condition in ['Принято ЕГАИС', 'Отклонено ЕГАИС']:
                del active_shipments[uuid]
                continue

            for file_id in list(ship.incomings_xml.keys()):
                #Checking if the file is parsed
                if ship.incomings_xml[file_id][1] != '': 
                    condition = ship.condition
                    ship.parsing_incoming_doc(file_id)
                    if ship.condition != condition: db.update_record_shipment(ship)
        
        # Перенести в отдельный поток
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
            else: 
                acts[row_id] += 1
                if acts[row_id] > 240: del acts[row_id]
        sleep(5)
   
def signal(name_audio) -> None:
    audio_file = get_file_path(name_audio)
    mixer.init()
    mixer.music.load(audio_file)
    mixer.music.play(2)

def error_parsing(xml, name, err): 
    with open(f'failed_parse/{name} {datetime.strftime(datetime.now(), "%Y-%m-%d %H-%M-%S")}.xml', 
              'w+', encoding='utf-8') as f: f.write(xml)
    logger.error(f'Ошибка парсинга: {err}. Имя файла: {name}.')