from datetime import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from tg_bot.services.shipments_in_bot import select_ships_per_day
from tg_bot.handlers.response import send_response, send_response_on_msg
from app.logs import logger

class Pick_ship(StatesGroup):
    waiting_for_pick_date = State()


async def send_date_picker(callback: types.CallbackQuery, state: FSMContext) -> types.Message:
    text = 'Укажите дату в формате ГГГГ-ММ-ДД'
    await state.set_state(Pick_ship.waiting_for_pick_date.state)
    await send_response(callback, text, kb_name='today_kb')

async def format_ships_per_day(date):
    ships = await select_ships_per_day(date)
    if len(ships) == 0:
        text = 'Нет отгрузок за выбранную дату'
        return text
    
    text = ''
    for ship in ships.values():
        text += (f"*№{ship['num']}* | {ship['condition']} | \n"
                 f"{ship['ttn']} | {ship['fix_number']}\n"
                 f"{ship['client_id']} | {ship['cl_name']}\n"
                 f"{ship['train_company']} | {ship['driver']} "
                 f"{ship['transport_number']} | {ship['train_trailer']}\n\n")

    text += f'*Всего отгрузок за дату:* {len(ships.keys())}'
    return text

@logger.catch
async def today_date(callback: types.CallbackQuery, state: FSMContext) -> types.Message:
    now = datetime.today()
    text = await format_ships_per_day(now)    
    await state.finish()
    await send_response(callback, text, kb_name='act_ships_kb')
    await callback.answer()

@logger.catch
async def written_date(message: types.Message, state: FSMContext) -> types.Message:
    try:
        date = datetime.strptime(message.text, '%Y-%m-%d').date()
    except TypeError as err:
        text = 'Укажите дату в формате ГГГГ-ММ-ДД'
        await send_response(message, text, kb_name='act_ships_kb')
        return
    text = await format_ships_per_day(date)
    
    await state.finish()
    await send_response_on_msg(message, text, kb_name='act_ships_kb')