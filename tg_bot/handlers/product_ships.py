from aiogram import types
from tg_bot.services.users import users
from tg_bot.services.shipments_in_bot import select_ship, select_cart_pr
from tg_bot.handlers.response import send_response
from app.logs import logger


@logger.catch
async def send_pr_ship(call: types.CallbackQuery, callback_data: dict) -> types.Message:
    logger.info(f'BOT: {call.from_user.id}: {users[call.from_user.id]["family"]} '
        f'{users[call.from_user.id]["name"]}. Запрос продукции')
    id_ship = int(callback_data['id_ship'])
    ship = await select_ship(id_ship)
    text = (f"*№{str(ship['num']).rjust(6, '0')}* | {ship['condition']}\n"
            f"{str(ship['client_id']).rjust(12, '0')} | {ship['full_name']}\n"
            f"{ship['ttn']} | {ship['fix_number']} \n\n *Транспорт:*\n"
            f"{ship['train_company']} \n{ship['transport_number']} \n"
            f"*Прицеп* - {ship['train_trailer']} \n{ship['driver']}\n\n*Продукция:*\n")   
    
    cart_products = await select_cart_pr(id_ship)
    for product in cart_products:
        text += (f'*{product["positions"]}* | *{str(product["product_id"]).rjust(19, "0")}* '
                f'| {product["full_name"]} |\n'
                f'{round(float(product["capacity"]), 2)} | {product["alcovolume"]} | {product["quantity"]} |\n'
                f'Дата розлива: {product["bottling_date"].strftime("%d.%m.%Y")} \n'
                f'*form-1:* {product["form1"]} \n'
                f'*old:* {product["form2_old"]} | \n*new:* {product["form2_new"]}\n \n')

    await send_response(call, text, 'act_ships_kb')