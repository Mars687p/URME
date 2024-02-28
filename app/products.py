from decimal import Decimal
from datetime import datetime
from bs4 import BeautifulSoup

from app.logs import logger
from app.services import Doc_utm, signal, error_parsing



class Product(Doc_utm):
    def __init__(self) -> None:
        self.products: dict = {}
        self.incomings_xml: dict = {}

    def parsing_incoming_doc(self, file_id):
        soup = BeautifulSoup(self.incomings_xml[file_id][1], 'lxml-xml')
        if 'ReplyAP' in self.incomings_xml[file_id][0]:                     
            for index, row in enumerate(soup.find_all('Product')):
                if row.find('Producer') != None:
                    
                    self.products[index] = {'alcocode': int(row.find('AlcCode').text.rstrip()),
                                            'name': row.find('FullName').text.rstrip().replace("'", "''"),
                                            'type_code': int(row.find('ProductVCode').text.rstrip()),
                                            'alcovolume': Decimal(row.find('AlcVolume').text),}
                    
                    try: 
                        self.products[index]['type_product'] = row.find('Type').text.rstrip()
                    except AttributeError:
                        self.products[index]['type_product'] = 'АП'
                    try:
                        self.products[index]['capacity'] = Decimal(row.find('Capacity').text)
                    except AttributeError:
                        self.products[index]['capacity'] = None
                    
                    try:
                        producer = row.find('Producer') 
                        self.products[index]['manufacturer'] = {
                                                'fsrar_id': int(producer.find('ClientRegId').text.rstrip()),
                                                'name': producer.find('FullName').text.rstrip().replace("'", "''"),
                                                'address': producer.find('description').text,}
                    except AttributeError:
                        self.products[index]['manufacturer'] = {
                                                'fsrar_id': None,
                                                'name': None,
                                                'address': None}
                    try:
                        self.products[index]['manufacturer']['INN'] = soup.find('wb:Consignee').find('oref:INN').text
                        self.products[index]['manufacturer']['KPP'] =  soup.find('wb:Consignee').find('oref:KPP').text
                    except AttributeError:
                        self.products[index]['manufacturer']['INN'] = None
                        self.products[index]['manufacturer']['KPP'] = None
           
        self.incomings_xml[file_id][1] = ''


class Handler_prod_docs:
    def __init__(self, db) -> None:
        self.db = db

    async def insert_db(self, pr: Product) -> None:
        async with self.db.pool.acquire() as con: 
            async with con.transaction() as tr:  
                for index in pr.products.keys():    
                    await pr.check_client(pr.products[index]['manufacturer'], con)
                    await pr.check_product(pr.products[index], con)



        logger.info(f'Обновление справочников продукции.')
        return True


    async def processing_in_products(self, msg) -> tuple:
        result = False
        pr = Product()
        pr.incomings_xml[msg['id_doc']] = [msg['type_file'], msg['xml']]
        #Checking if the file is parsed
        if pr.incomings_xml[msg['id_doc']][1] != '':  
            pr.parsing_incoming_doc(msg['id_doc'])
            result = await self.insert_db(pr)
            
        if result: return True
        return False
        
