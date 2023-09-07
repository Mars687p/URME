from loguru import logger

logger.add('logs.log', encoding='utf8', format='[{time:YYYY-MM-DD HH:mm:ss}] {level} {message}', 
            level='INFO', rotation="5 MB")
