from aiogram import types
from aiogram.utils.callback_data import CallbackData

from tg_bot.services.users import users

cb_pr_ship = CallbackData('kbf2', 'action', 'id_ship')


async def act_ships_kb(user_id: int) -> types.InlineKeyboardMarkup:
    ash_but = types.InlineKeyboardButton(text="Активные отгрузки",
                                         callback_data="bt_active_ships")
    kb = types.InlineKeyboardMarkup()
    kb.add(ash_but)
    if users[user_id]['access']['sh_per_day']:
        kb.add(types.InlineKeyboardButton(text="Отгрузки за дату",
                                          callback_data="bt_ships_day"))
    return kb


async def product_ship_kb(user_id: int,
                          id_ship: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if users[user_id]['access']['reg_form2']:
        form2_but = types.InlineKeyboardButton(
                        text='Продукция',
                        callback_data=cb_pr_ship.new(id_ship=id_ship,
                                                     action='form2'))
        kb.add(form2_but)
    return kb


async def today_kb(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if users[user_id]['access']['sh_per_day']:
        kb.add(types.InlineKeyboardButton(
                        text="Cегодня",
                        callback_data="today_date"))
    return kb
