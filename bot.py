import copy
import json
from typing import TYPE_CHECKING, Any, Dict

from aiogram import Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from tg_bot.handlers.active_ships import send_active_ships
from tg_bot.handlers.completed_car import send_completed_car
from tg_bot.handlers.completed_ship import send_completed_ship
from tg_bot.handlers.product_ships import send_pr_ship
from tg_bot.handlers.ships_per_date import (Pick_ship, send_date_picker,
                                            today_date, written_date)
from tg_bot.handlers.starts import send_help
from tg_bot.services.config_bot import (CONDITIONS, active_ships, bot,
                                        cars_num, db, loop, transports)
from tg_bot.services.keyboards import cb_pr_ship
from tg_bot.services.shipments_in_bot import select_active_ships
from tg_bot.services.transport import add_transports
from tg_bot.services.update_status_bot import update_status

if TYPE_CHECKING:
    import asyncpg

dp = Dispatcher(bot, storage=MemoryStorage())


async def register_handlers() -> None:
    dp.register_message_handler(send_help,
                                commands=['start', 'help'],
                                state='*')
    dp.register_callback_query_handler(send_pr_ship,
                                       cb_pr_ship.filter(action='form2'))
    dp.register_callback_query_handler(send_active_ships,
                                       text='bt_active_ships',
                                       state='*')
    dp.register_callback_query_handler(send_date_picker,
                                       text='bt_ships_day',
                                       state='*')
    dp.register_callback_query_handler(today_date,
                                       text='today_date',
                                       state=Pick_ship.waiting_for_pick_date)
    dp.register_message_handler(written_date,
                                state=Pick_ship.waiting_for_pick_date)


async def register_commands() -> None:
    await dp.bot.set_my_commands([types.BotCommand("help", "Помощь")])


async def listener(conn: 'asyncpg.Connection', pid: int,
                   chanel: str, raw_payload: str) -> None:
    payload: Dict[str, Any] = json.loads(raw_payload)
    if chanel == 'ships_insert_or_update':
        await update_list_active_ship(payload)
    elif chanel == 'tr_insert':
        global transports, cars_num
        transports, cars_num = await add_transports(payload, transports)


async def update_list_active_ship(payload: Dict[str, Any]) -> None:
    if payload['condition'] == CONDITIONS[0]:
        active_ships[payload['id']] = copy.deepcopy(payload)

    if (payload['id'] not in active_ships.keys() and
            payload['condition'] not in CONDITIONS[:2]):
        return

    for ship_id in list(active_ships.keys()):
        if payload['id'] == ship_id:
            active_ships[ship_id] = copy.deepcopy(payload)

            if active_ships[ship_id]['condition'] in CONDITIONS[2:4]:
                await send_completed_ship(active_ships[ship_id])
                del active_ships[ship_id]
                del transports[ship_id]
                for tr in tuple(cars_num):
                    if tr not in [i['tr_num'] for i in transports.values()]:
                        await send_completed_car(tr, payload['condition'])
                        cars_num.remove(tr)


if __name__ == '__main__':
    active_ships = loop.run_until_complete(select_active_ships())  # noqa: F811
    loop.create_task(register_handlers())
    loop.create_task(register_commands())
    loop.create_task(db.listen_db(listener))

    loop.create_task(update_status(True, 'tg_bot'))
    executor.start_polling(dp, skip_updates=True, timeout=120)
    loop.run_until_complete(update_status(False, 'tg_bot'))
    loop.run_until_complete(db.pool.close())
    loop.run_until_complete(db.conn.close())
    print('DB close')
