#for asyncpg
select_ships_per_day = """SELECT sh.id, sh.num, sh.condition, sh.ttn, sh.fix_number, 
                        sh.client_id, cl.full_name, tr.change_ownership, tr.train_company, 
                        tr.transport_number, tr.train_trailer, tr.train_customer,  
                        tr.driver, tr.unload_point FROM shipments as sh
                        JOIN clients as cl ON cl.fsrar_id = sh.client_id
                        JOIN transports as tr ON sh.id = tr.shipment_id
                        WHERE sh.date_creation = $1
                    """
select_active_ships = """SELECT sh.id, sh.num, sh.condition, sh.ttn, sh.fix_number, sh.date_creation, 
                        sh.client_id, cl.full_name FROM shipments as sh 
                        JOIN clients as cl ON sh.client_id = cl.fsrar_id 
                        where sh.condition in ($1, $2) 
                    """

select_ship_info ="""SELECT sh.num, sh.condition, sh.ttn, sh.fix_number, 
                    sh.client_id, cl.full_name, tr.change_ownership, tr.train_company, 
                    tr.transport_number, tr.train_trailer, tr.train_customer,  
                    tr.driver, tr.unload_point FROM shipments as sh
                    JOIN clients as cl ON cl.fsrar_id = sh.client_id
                    JOIN transports as tr ON sh.id = tr.shipment_id
                    WHERE sh.id = $1
                """

select_cart_products = """SELECT cpr.positions, cpr.product_id, pr.full_name, pr.capacity, pr.alcovolume, 
                        cpr.quantity, cpr.form1, cpr.form2_old, cpr.form2_new, cpr.bottling_date
                        FROM cart_products as cpr
                        JOIN products as pr ON cpr.product_id = pr.alcocode
                        WHERE cpr.shipment_id = $1
                        ORDER BY cpr.positions
                    """ 

select_users_bot = 'SELECT names, family, tg_id, tg_access FROM users'

#for psycopg2
select_active_shipments =  """SELECT id, condition, uuid, num FROM shipments
                              WHERE condition in ('Принято ЕГАИС(без номера фиксации)',
                                         'Отправлено');"""

select_cart_pr = """SELECT positions, form2_old FROM cart_products
                         WHERE shipment_id=%s;"""

select_product = """SELECT alcocode FROM products where alcocode = %s"""

select_client = """SELECT fsrar_id FROM clients WHERE fsrar_id = %s"""

insert_client = """INSERT INTO clients(full_name, fsrar_id, inn, kpp, adress)
                         VALUES (%s, %s, %s, %s, %s);"""

insert_shipment = """INSERT INTO shipments(num, condition, uuid, date_creation, client_id) 
                     VALUES (%s, %s, %s, %s, %s) RETURNING id;"""

insert_transport = """INSERT INTO transports(shipment_id, change_ownership, 
                     train_company, transport_number, train_trailer, train_customer, 
                     driver, unload_point) VALUES (%s, %s, %s,  %s, %s, %s, %s, %s);""" 

insert_product = """INSERT INTO products(alcocode, full_name, capacity, alcovolume, 
                    type_product, type_code) VALUES (%s, %s, %s, %s, %s, %s);"""

insert_cart_products = """INSERT INTO cart_products(shipment_id, product_id, positions, quantity, 
                         price_for_one, form2_old, form1) VALUES (%s, %s, %s, %s, %s, %s, %s);"""

update_shipment_regf2 = """UPDATE shipments SET condition = %s, ttn = %s,
                         fix_number = %s WHERE id=%s;"""
update_shipment_partly = """UPDATE shipments SET condition = %s, 
                            date_fixation = %s WHERE ttn = %s"""
update_shipment_cond = """UPDATE shipments SET condition = %s WHERE id=%s;"""

update_cart_products = """UPDATE cart_products SET form2_new = %s, bottling_date = %s
                             WHERE shipment_id=%s and positions = %s;"""

update_cart_product_partly = """UPDATE cart_products SET quantity = %s WHERE form2_new = %s"""