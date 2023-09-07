from aiogram import types
from tg_bot.services.config_bot import CONDITIONS
from tg_bot.services.users import users
from tg_bot.handlers.response import send_message

async def send_completed_ship(ship) -> types.Message:
        for id, user in users.items():
            if ship['condition'] == CONDITIONS[2]:
                if user['access']['sms_acc']:
                    text = (f"Отгрузка №{ship['num']} зафиксирована. ({ship['cl_full_name']})")                    
                    await send_message(id, text, 'product_ship_kb', ship['id'])

            if ship['condition'] == CONDITIONS[3]:
                if user['access']['sms_acc']:
                    text = (f"Отгрузка №{ship['num']} отклонена")
                    await send_message(id, text, 'act_ships_kb')