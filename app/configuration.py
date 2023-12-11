import sys, os
import configparser
from app.logs import logger


def get_url_utm() -> str:
    return config.get('Settings', 'url_utm')

def get_file_path(name_file) -> str:
    return config.get('Audio', name_file)

def get_bot_token() -> str:
    return config.get('Telegram', 'token')

def get_condition_ships() -> tuple:
    return eval(config.get('Telegram', 'condition_ships'))

def get_conection_database(user) -> str:
    return {'db_name': config.get('Database', 'db_name'),
            'host': config.get('Database', 'host'),
            'port': config.get('Database', 'port'),
            'user': user,
            'password': config.get('Users_db', user)}

try:
    path_file = os.path.realpath(__file__)
    dir_path = os.path.dirname(path_file)
    config = configparser.ConfigParser()
    config.read(f'{dir_path}\\config.ini', encoding="utf-8")
except Exception as e:
    logger.exception(e)
    sys.exit()

