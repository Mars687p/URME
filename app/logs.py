import os
from loguru import logger


path_dir = os.path.dirname(os.path.realpath(__file__)).split('\\')
path_dir = '\\'.join(i for i in path_dir[:len(path_dir)-1])
logger.add(f'{path_dir}\\logs.log', encoding='utf8', format='[{time:YYYY-MM-DD HH:mm:ss}] {level} {message}', 
            level='INFO', rotation="5 MB")
