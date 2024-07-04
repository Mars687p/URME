import os
import traceback
from datetime import datetime

from pygame import error, mixer

from app.configuration import get_file_path
from app.logs import logger


def signal(name_audio: str) -> None:
    try:
        audio_file = get_file_path(name_audio)
        mixer.init()
        mixer.music.load(audio_file)
        mixer.music.play(2)
    except error:
        pass


def writing_file_an_err(xml: str, name: str) -> None:
    path_file = os.path.realpath(__file__)
    dir_path = os.path.dirname(path_file).replace('app', '')
    name_file = f'{name} {datetime.strftime(datetime.now(), "%Y-%m-%d %H-%M-%S")}'
    with open(f'{dir_path}\\failed_parse\\{name_file}.xml',
              'w+', encoding='utf-8') as f:
        f.write(xml)
    err = traceback.format_exc()
    logger.error(f'Ошибка {err} Имя файла: {name_file}')
