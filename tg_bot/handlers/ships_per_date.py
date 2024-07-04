from datetime import date, datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.logs import logger
from tg_bot.handlers.response import send_response, send_response_on_msg
from tg_bot.services.shipments_in_bot import select_ships_per_day


class Pick_ship(StatesGroup):
    waiting_for_pick_date = State()


async def send_date_picker(callback: types.CallbackQuery,
                           state: FSMContext) -> None:
    text = 'Укажите дату в формате ГГГГ-ММ-ДД'
    await state.set_state(Pick_ship.waiting_for_pick_date.state)
    await send_response(callback, text, kb_name='today_kb')


async def format_ships_per_day(input_date: date) -> str:
    ships = await select_ships_per_day(input_date)
    if len(ships) == 0:
        text = 'Нет отгрузок за выбранную дату'
        return text

    text = ''
    for ship in ships.values():
        text += (f"*№{str(ship['num']).rjust(6, '0')}* | {ship['condition']} | \n"
                 f"{ship['ttn']} | {ship['fix_number']}\n"
                 f"{ship['client_id']} | {ship['cl_name']}\n"
                 f"{ship['train_company']} | {ship['driver']} "
                 f"{ship['transport_number']} | {ship['train_trailer']}\n\n")

    text += f'*Всего отгрузок за дату:* {len(ships.keys())}'
    return text


@logger.catch
async def today_date(callback: types.CallbackQuery, state: FSMContext) -> None:
    now = datetime.today()
    text = await format_ships_per_day(now)
    await state.finish()
    await send_response(callback, text, kb_name='act_ships_kb')
    await callback.answer()


@logger.catch
async def written_date(message: types.Message,
                       state: FSMContext) -> None:
    try:
        input_date = datetime.strptime(message.text, '%Y-%m-%d').date()
    except TypeError:
        text = 'Укажите дату в формате ГГГГ-ММ-ДД'
        await send_response(message, text, kb_name='act_ships_kb')
        return
    text = await format_ships_per_day(input_date)

    await state.finish()
    await send_response_on_msg(message, text, kb_name='act_ships_kb')
