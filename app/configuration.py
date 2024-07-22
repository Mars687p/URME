import configparser
import os
import sys
from typing import Dict

from app.logs import logger


def get_url_utm() -> str:
    return config.get('Settings', 'url_utm')


def get_fsrar_id() -> int:
    return config.getint('Settings', 'fsrar_id')


def get_file_path(name_file: str) -> str:
    return config.get('Audio', name_file)


def get_bot_token() -> str:
    return config.get('Telegram', 'token')


def get_condition_ships() -> tuple:
    return eval(config.get('Telegram', 'condition_ships'))


def get_conection_database(user: str) -> Dict[str, str]:
    return {'db_name': config.get('Database', 'db_name'),
            'host': config.get('Database', 'host'),
            'port': config.get('Database', 'port'),
            'user': user,
            'password': config.get('Users_db', user)}


def get_data_connection_rabbit() -> dict:
    return {'name_pc': config.get('Rabbit', 'pc'),
            'user': config.get('Rabbit', 'user'),
            'password': config.get('Rabbit', 'password')}


def get_start_app() -> bool:
    return config.getboolean('Settings', 'legacy_start')


def get_django_key() -> str:
    return config.get('Django', 'key')


def get_automatic_print() -> bool:
    return config.getboolean('Settings', 'automatic_print')


try:
    path_file = os.path.realpath(__file__)
    dir_path = os.path.dirname(path_file)
    config = configparser.ConfigParser(interpolation=None)
    config.read(f'{dir_path}\\config.ini', encoding="utf-8")
except Exception as _err:
    logger.error(_err)
    sys.exit()
