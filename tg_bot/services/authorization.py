from typing import Callable

from aiogram.types import Message

from app.logs import logger
from tg_bot.services.users import users


def auth(func: Callable) -> Callable:
    async def wrapper(message: Message) -> Callable | Message:
        if message['from']['id'] not in users.keys():
            logger.warning(f'{message.from_user.username}: {message.from_user.id}.'
                           f'Несанкционированная попытка входа в бота')
            return await message.answer('Несанкционированная попытка входа')
        return await func(message)
    return wrapper
