from tg_bot.services.config_bot import CONDITIONS, db, transports
from tg_bot.services.transport import select_tr
from templates import query 


async def select_ships_per_day(date) -> dict:
    ships = await db.select_sql(query.select_ships_per_day, date)
    ships = {ship['id']: {'num': ship['num'],
                                 'condition': ship['condition'],
                                 'train_company': ship['train_company'],
                                 'transport_number': ship['transport_number'],
                                 'train_trailer': ship['train_trailer'],
                                 'driver': ship['driver'],
                                 'transport_number': ship['transport_number'],
                                 'transport_number': ship['transport_number'],
                                 'transport_number': ship['transport_number'],
                                 'client_id': ship['client_id'],
                                 'cl_name': ship['full_name'],
                                 'ttn': ship['ttn'],
                                 'fix_number': ship['fix_number']}
                                 for ship in ships}
    return ships

async def select_active_ships() -> dict:
    ships = await db.select_sql(query.select_active_ships, *CONDITIONS[:2])
    ships = {ship['id']: {'num': ship['num'],
                                 'condition': ship['condition'],
                                 'client': ship['client_id'],
                                 'cl_name': ship['full_name'],
                                 'ttn': ship['ttn'],
                                 'fix_num': ship['fix_number'],
                                 'date': ship['date_creation'].strftime('%d.%m.%Y')}
                                 for ship in ships}
    if len(ships) > 0:
        for id_ship in ships.keys():
            global transports
            transports = await select_tr(id_ship)
    return ships

async def select_ship(id_ship: int) -> dict:
    ship = await db.select_sql(query.select_ship_info, id_ship)
    return ship[0]

async def select_cart_pr(id_ship: int) -> list:
    cart_products = await db.select_sql(query.select_cart_products, id_ship)
    return cart_products