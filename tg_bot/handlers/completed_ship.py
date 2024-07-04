from typing import Any, Dict

from tg_bot.handlers.response import send_message
from tg_bot.services.config_bot import CONDITIONS
from tg_bot.services.users import users


async def send_completed_ship(ship: Dict[str, Any]) -> None:
    for id, user in users.items():
        if ship['condition'] == CONDITIONS[2]:
            if user['access']['sms_acc']:
                text = (f"Отгрузка №{str(ship['num']).rjust(6, '0')} "
                        f"зафиксирована. ({ship['cl_name']})")
                await send_message(id, text, 'product_ship_kb', ship['id'])

        elif ship['condition'] == CONDITIONS[3]:
            if user['access']['sms_acc']:
                text = f"Отгрузка №{ship['num']} отклонена"
                await send_message(id, text, 'act_ships_kb')
