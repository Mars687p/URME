import json
from tg_bot.services.config_bot import loop, db
from templates import query 


def get_users() -> dict:
    return {int(user['tg_id']): {'name':user['first_name'], 
                                'family': user['last_name'],
                                'access': json.loads(user['tg_access'])} 
                                for user in loop.run_until_complete(
                                    db.select_sql(query.select_users_bot)) 
                                    if user['tg_id'] != None}

users = get_users()