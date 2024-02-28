import traceback
import os
from datetime import datetime
from pygame import mixer, error

from app.configuration import get_file_path, get_fsrar_id
from app.logs import logger
from templates import query


class Doc_utm:
    def __init__(self, uuid, outgoing_xml, condition='Отправлено') -> None:
        self.uuid = uuid
        self.outgoing_xml = outgoing_xml
        self.incomings_xml: dict = {}
        self.condition: str = condition
        self.number: str = ''
        self.products: dict = {}
        self.fixation: dict = {}
        self.footing: str = ''
        self.id_in_base = None
        #for ships
        self.transport: dict = {}
        self.client: dict = {}
        #for mf
        self.date_production = None
    
    async def check_client(self, client, con):
        if client['fsrar_id'] != None:
            fsrar_id = await con.fetchval(query.select_client_async, client['fsrar_id'])
            if fsrar_id == None:
                await con.execute(query.insert_client_async, client['name'], client['fsrar_id'], 
                                        int(client['INN']), int(client['KPP']), 
                                        client['address'])

    async def check_product(self, product, con):
        alcocode = await con.fetchval(query.select_product_async, product['alcocode'])
        if alcocode == None: 
            own_fsrar_id = get_fsrar_id()
            if product['manufacturer']['fsrar_id'] == own_fsrar_id:
                is_own = True
            else: is_own = False
            await con.execute(query.insert_product_async, product['alcocode'], product['name'], 
                                    product['capacity'], product['alcovolume'], 
                                    product['type_product'], product['type_code'], 
                                    product['manufacturer']['fsrar_id'], is_own)



def signal(name_audio) -> None:
    try:
        audio_file = get_file_path(name_audio)
        mixer.init()
        mixer.music.load(audio_file)
        mixer.music.play(2)
    except error:
        pass


def error_parsing(xml, name):
    path_file = os.path.realpath(__file__)
    dir_path = os.path.dirname(path_file).replace('app', '')
    name_file = f'{name} {datetime.strftime(datetime.now(), "%Y-%m-%d %H-%M-%S")}'
    with open(f'{dir_path}\\failed_parse\\{name_file}.xml', 
              'w+', encoding='utf-8') as f: f.write(xml)
    err = traceback.format_exc()
    logger.error(f'Ошибка {err} Имя файла: {name_file}')
