import json
from typing import Dict

from custom_types.users import User, UserAccess
from templates import query
from tg_bot.services.config_bot import db, loop


def get_users() -> Dict[int, User]:
    return {int(user['tg_id']): User({
                                'name': user['first_name'],
                                'family': user['last_name'],
                                'access': UserAccess(
                                            json.loads(user['tg_access']))  # type: ignore
                                    })
            for user in loop.run_until_complete(
                        db.select_sql(query.select_users_bot))
            if user['tg_id'] is not None
            }


users = get_users()
