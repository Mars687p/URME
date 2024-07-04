import copy
from typing import Any, Dict

from tg_bot.services.config_bot import db


async def select_tr(id_ship: int) -> Dict[str, Any]:
    sql = "SELECT * FROM transports WHERE shipment_id = $1"
    cars = await db.select_sql(sql, id_ship)
    return {
            'change_ownership': cars[0]["change_ownership"],
            'company': cars[0]["train_company"],
            'tr_num': cars[0]["transport_number"],
            'trailer': cars[0]["train_trailer"],
            'customer': cars[0]["train_customer"],
            'driver': cars[0]["driver"],
            'unload_point': cars[0]["unload_point"]
            }


async def add_transports(payload: Dict[str, Any],
                         transports: Dict[str, Any]) -> tuple[Dict[str, Any], set]:
    transports[payload['sh_id']] = copy.deepcopy(payload)
    cars_num = {i['tr_num'] for i in transports.values()}
    return transports, cars_num
