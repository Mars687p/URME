from aiogram import types

from tg_bot.handlers.response import send_response_on_msg
from tg_bot.services.authorization import auth
from tg_bot.services.users import users


@auth
async def send_help(message: types.Message) -> None:
    text = (f'Здравствуй, {users[message["from"]["id"]]["name"]}!\n'
            f'/start, /help - вызвать помощника')
    await send_response_on_msg(message, text, 'act_ships_kb')
