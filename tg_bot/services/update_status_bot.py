import datetime

from templates import query
from tg_bot.services.config_bot import db


async def update_status(states: bool, module_name: str) -> None:
    times = datetime.datetime.now()
    if states:
        await db.update_sql(query.update_status_tg_bot_start, states, times, None, module_name)
    else:
        await db.update_sql(query.update_status_tg_bot_end, states, times, module_name)
