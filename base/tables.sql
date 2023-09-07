CREATE TABLE clients (fsrar_id BIGINT primary key,
					  full_name varchar(255) NOT NULL,
					  inn varchar(30),
					  kpp varchar(30),
					  adress text);

CREATE TABLE products (alcocode BIGINT primary key,
					   full_name varchar(255) NOT NULL,
					   capacity real,
					   alcovolume real NOT NULL,
					   type_product varchar(255) NOT NULL,
					   type_code integer NOT NULL);

CREATE TABLE shipments (id serial primary key,
					    num varchar(10) NOT NULL,
						condition varchar(40) NOT NULL,
						uuid uuid,
						ttn varchar(50),
						fix_number varchar(50),
						date_creation date NOT NULL,
						date_fixation date,
						client_id BIGINT references clients(fsrar_id));

CREATE TABLE transports (id serial primary key,
						 shipment_id integer references shipments(id),
						 change_ownership varchar(30),
						 train_company varchar(255),
						 transport_number varchar(50),
						 train_trailer varchar(50),
						 train_customer varchar(255),
						 driver varchar(255),
						 unload_point text);

CREATE TABLE cart_products (id serial primary key,
							product_id BIGINT references products(alcocode),
							shipment_id integer references shipments(id),
					   		positions varchar(3) NOT NULL,
							quantity integer NOT NULL,
							price_for_one numeric NOT NULL,
							bottling_date date,
							form1 varchar(18) NOT NULL,
							form2_old varchar(18) NOT NULL,
							form2_new varchar(18));

CREATE TABLE users (id serial primary key,
					family varchar(255) NOT NULL,
					names varchar(255) NOT NULL,
					username varchar(100),
					pass varchar(100) NOT NULL,
					tg_id BIGINT,
					access json)
