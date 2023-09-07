from aiogram import types
from tg_bot.services.config_bot import CONDITIONS
from tg_bot.services.users import users
from tg_bot.handlers.response import send_message

async def send_completed_car(tr_num, condition) -> types.Message:
    for id, user in users.items():
        if user['access']['fix_car'] and condition == CONDITIONS[2]:
            text = (f"ТС с рег. номером {tr_num} зафиксировано")
            await send_message(id, text, 'act_ships_kb')