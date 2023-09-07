from aiogram import types
from tg_bot.services.authorization import auth
from tg_bot.services.users import users
from tg_bot.services.shipments_in_bot import select_active_ships
from tg_bot.handlers.response import send_response
from app.logs import logger


@auth
async def send_active_ships(callback: types.CallbackQuery) -> types.Message:
    logger.info(f'BOT: {callback.from_user.id}: {users[callback.from_user.id]["family"]} '
                f'{users[callback.from_user.id]["name"]}. Запрос активных отгрузок')   
    active_ships = await select_active_ships()
    text = ''
    if len(active_ships) == 0:
        text = 'Нет активных отгрузок'
        await send_response(callback, text)
        return

    for ship in active_ships.values():
        text += (f"*№{ship['num']}* | {ship['condition']} | \n"
                 f"{ship['cl_name']} | {ship['date']}\n\n")

    text += f'*Всего активных отгрузок:* {len(active_ships)}'
    await send_response(callback, text)