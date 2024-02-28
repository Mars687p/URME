import re
from aiogram import types
from tg_bot.services.keyboards import act_ships_kb, product_ship_kb, today_kb
from tg_bot.services.config_bot import bot


async def escaping_characters(text) -> str:  
    return re.sub(r'(?=[\!\-\|\.\(\)<>+=])', r'\\', text)

async def is_long_message(text):
    if len(text) > 4095:
        lst_sms = []
        for x in range(0, len(text), 4095):
            lst_sms.append(text[x:x+4095])
        return lst_sms
    return text

async def format_message(usr_id: int, text: str, kb_name: str,
                         ship_id=0) -> tuple[types.InlineKeyboardMarkup, str]:
    if kb_name == 'product_ship_kb':
        kb = await product_ship_kb(usr_id, ship_id)
    if kb_name == 'today_kb':
        kb = await today_kb(usr_id)
    if kb_name in ['act_ships_kb', '']:
        kb = await act_ships_kb(usr_id)
    text = await escaping_characters(text)
    text = await is_long_message(text)
    return kb, text

async def send_response(callback: types.CallbackQuery, text: str, kb_name='') -> types.Message:
    kb, text = await format_message(callback.from_user.id, text, kb_name)
    if type(text) == list:
        for sms in text:
            await callback.message.answer(sms, reply_markup=kb) 
    else: await callback.message.answer(text, reply_markup=kb) 
    await callback.answer()

async def send_response_on_msg(message: types.Message, text: str, kb_name='') -> types.Message:
    kb, text = await format_message(message["from"]["id"], text, kb_name)
    if type(text) == list:
        for sms in text:
            await message.answer(sms, reply_markup=kb) 
    else: await message.answer(text, reply_markup=kb) 

async def send_message(usr_id: int, text: str, kb_name='', ship_id=0) -> types.Message:
    kb, text = await format_message(usr_id, text, kb_name, ship_id)
    if type(text) == list:
        for sms in text:
            await bot.send_message(usr_id, sms, reply_markup=kb)
    else: await bot.send_message(usr_id, text, reply_markup=kb)




