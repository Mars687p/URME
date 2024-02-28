import asyncio
from aiogram import Bot

from base.database import Async_database
from app.configuration import get_bot_token, get_condition_ships


CONDITIONS = get_condition_ships()

bot = Bot(token=get_bot_token(), parse_mode='MarkdownV2')
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
db = Async_database('tg_bot', loop)
loop.run_until_complete(db.get_connection())

transports: dict = {}
active_ships: dict = {}
cars_num: set = set()