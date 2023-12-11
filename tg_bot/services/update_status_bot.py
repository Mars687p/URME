import datetime
from tg_bot.services.config_bot import db
from templates import query

async def update_status(states, module_name):
    times = datetime.datetime.now()
    if states:
        await db.update_sql(query.update_status_tg_bot_start, states, times, None, module_name)
    else: 
        await db.update_sql(query.update_status_tg_bot_end, states, times, module_name)
