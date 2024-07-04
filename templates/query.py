# for asyncpg
select_ships_per_day = """SELECT sh.id, sh.num, sh.condition, sh.ttn, sh.fix_number,
                        sh.date_creation,
                        sh.client_id, cl.full_name, tr.change_ownership, tr.train_company,
                        tr.transport_number, tr.train_trailer, tr.train_customer,
                        tr.driver, tr.unload_point
                        FROM shipments as sh
                        JOIN clients as cl ON cl.fsrar_id = sh.client_id
                        JOIN transports as tr ON sh.id = tr.shipment_id
                        WHERE sh.date_creation = $1
                    """
select_active_ships = """SELECT sh.id, sh.num, sh.condition, sh.ttn, sh.fix_number,
                        sh.date_creation,
                        sh.client_id, cl.full_name FROM shipments as sh
                        JOIN clients as cl ON sh.client_id = cl.fsrar_id
                        where sh.condition in ($1, $2)
                    """

select_ship_info = """SELECT sh.num, sh.condition, sh.ttn, sh.fix_number,
                    sh.client_id, cl.full_name, tr.change_ownership, tr.train_company,
                    tr.transport_number, tr.train_trailer, tr.train_customer,
                    tr.driver, tr.unload_point FROM shipments as sh
                    JOIN clients as cl ON cl.fsrar_id = sh.client_id
                    JOIN transports as tr ON sh.id = tr.shipment_id
                    WHERE sh.id = $1
                """

select_cart_products = """SELECT cpr.positions, cpr.product_id, pr.full_name, pr.capacity,
                        pr.alcovolume,
                        cpr.quantity, cpr.form1, cpr.form2_old, cpr.form2_new, cpr.bottling_date
                        FROM cart_products as cpr
                        JOIN products as pr ON cpr.product_id = pr.alcocode
                        WHERE cpr.shipment_id = $1
                        ORDER BY cpr.positions
                    """

select_users_bot = 'SELECT first_name, last_name, tg_id, tg_access FROM users'

update_status_tg_bot_start = """UPDATE status_modules SET states = $1, time_start = $2,
                                time_end = $3 WHERE names = $4"""

update_status_tg_bot_end = """UPDATE status_modules SET states = $1, time_end = $2
                                WHERE names = $3"""

select_product_async = """SELECT alcocode FROM products where alcocode = $1"""

# shipments query
select_active_shipments = """SELECT id, condition, uuid, num FROM shipments
                              WHERE condition in ('Принято ЕГАИС(без номера фиксации)',
                                         'Отправлено');"""

select_cart_pr_async = """SELECT positions, form2_old FROM cart_products
                         WHERE shipment_id=$1;"""

select_product_async = """SELECT alcocode FROM products where alcocode = $1"""

select_client_async = """SELECT fsrar_id, adress FROM clients WHERE fsrar_id = $1"""

select_transports_async = 'SELECT * FROM transports where shipment_id =$1'

insert_client_async = """INSERT INTO clients(full_name, fsrar_id, inn, kpp, adress)
                         VALUES ($1, $2, $3, $4, $5);"""

update_client_async = """UPDATE clients SET adress = $1 WHERE fsrar_id=$2"""

insert_shipment_async = """INSERT INTO shipments(num, condition, uuid,
                                        date_creation, client_id, footing)
                     VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;"""

insert_transport_async = """INSERT INTO transports(shipment_id, change_ownership,
                     train_company, transport_number, train_trailer, train_customer,
                     driver, unload_point) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);"""

insert_product_async = """INSERT INTO products(alcocode, full_name, capacity, alcovolume,
                    type_product, type_code, manufacturer_id, local_reference)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8);"""

insert_cart_products_async = """INSERT INTO cart_products(shipment_id, product_id,
                            positions, quantity,
                            price_for_one, form2_old, form1)
                            VALUES ($1, $2, $3, $4, $5, $6, $7);"""

update_shipment_regf2_async = """UPDATE shipments SET condition = $1, ttn = $2,
                         fix_number = $3 WHERE id=$4;"""

update_shipment_partly_async = """UPDATE shipments SET condition = $1,
                            date_fixation = $2 WHERE ttn = $3"""

update_shipment_cond_async = """UPDATE shipments SET condition = $1 WHERE id=$2;"""

update_cart_products_async = """UPDATE cart_products SET form2_new = $1, bottling_date = $2
                             WHERE shipment_id=$3 and positions = $4;"""

update_cart_product_partly_async = """UPDATE cart_products SET quantity = $1
                                    WHERE form2_new = $2"""


# manufacture query
insert_record_manufactures = """INSERT INTO manufactures_manufactures(num, condition, uuid,
                                date_creation, date_production, type_operation, footing)
                                VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id;"""

insert_manufactured_pr = """INSERT INTO manufactures_manufacturedproducts(manufactures_id,
                            product_id, positions, quantity,
                            batch_num, alcovolume) VALUES ($1, $2, $3, $4, $5,  $6)
                            RETURNING id;"""

insert_raw_pr = """INSERT INTO manufactures_rawformanufactured(mf_products_id,
                    product_id, positions, quantity, form2)
                    VALUES ($1, $2, $3, $4, $5);"""

select_active_mf = """SELECT id, condition, uuid, num FROM manufactures_manufactures
                              WHERE condition in ('Принято ЕГАИС', 'Отправлено');"""

select_mf_product_async = """SELECT positions FROM manufactures_manufacturedproducts
                         WHERE manufactures_id=$1;"""

update_mf_act = """UPDATE manufactures_manufactures SET condition = $1,
                            date_fixation = $2 WHERE reg_number = $3"""

update__mfed_products = """UPDATE manufactures_manufacturedproducts SET form1 = $1, form2 = $2
                             WHERE manufactures_id=$3 and positions = $4;"""

update__mf_regdata = """UPDATE manufactures_manufactures SET reg_number = $1, date_fixation = $2
                                WHERE id=$3;"""

update_mf_cond = """UPDATE manufactures_manufactures SET condition = $1 WHERE id=$2;"""

update_mf_wbf_num = """UPDATE manufactures_manufactures SET fix_number = $1
                        WHERE date_production=$2 and num=$3;"""


# for psycopg2
# legacy query
select_mf_product = """SELECT positions FROM manufactures_manufacturedproducts
                         WHERE manufactures_id=%s;"""

select_cart_pr = """SELECT positions, form2_old FROM cart_products
                         WHERE shipment_id=%s;"""

select_product = """SELECT alcocode FROM products where alcocode = %s"""

select_client = """SELECT fsrar_id FROM clients WHERE fsrar_id = %s"""

select_transports = 'SELECT * FROM transports where shipment_id =%s'

insert_client = """INSERT INTO clients(full_name, fsrar_id, inn, kpp, adress)
                         VALUES (%s, %s, %s, %s, %s);"""

insert_shipment = """INSERT INTO shipments(num, condition, uuid, date_creation, client_id, footing)
                     VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;"""

insert_transport = """INSERT INTO transports(shipment_id, change_ownership,
                     train_company, transport_number, train_trailer, train_customer,
                     driver, unload_point) VALUES (%s, %s, %s,  %s, %s, %s, %s, %s);"""

insert_product = """INSERT INTO products(alcocode, full_name, capacity, alcovolume,
                    type_product, type_code, manufacturer_id, local_reference)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""

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

update_status_modules = """UPDATE status_modules SET states = %s, time_start = %s, time_end = %s
                            WHERE names = %s"""
