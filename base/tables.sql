CREATE TABLE clients (fsrar_id BIGINT primary key,
					  full_name varchar(255) NOT NULL,
					  inn BIGINT,
					  kpp BIGINT,
					  adress text);

CREATE TABLE products (alcocode BIGINT primary key,
					   full_name varchar(255) NOT NULL,
					   capacity numeric,
					   alcovolume numeric NOT NULL,
					   real_alcovolume numeric,
					   type_product varchar(255) NOT NULL,
					   type_code integer NOT NULL);

CREATE TABLE shipments (id serial primary key,
					    num BIGINT NOT NULL,
						condition varchar(40) NOT NULL,
						uuid uuid,
						ttn varchar(50),
						fix_number varchar(50),
						date_creation date NOT NULL,
						date_fixation date,
						client_id BIGINT references clients(fsrar_id),
						footing text);

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
							shipment_id BIGINT references shipments(id),
					   		positions varchar(3) NOT NULL,
							quantity numeric NOT NULL,
							price_for_one numeric NOT NULL,
							bottling_date date,
							form1 varchar(18),
							form2_old varchar(18) NOT NULL,
							form2_new varchar(18));

CREATE TABLE users (id serial primary key,
					family varchar(255),
					names varchar(255) NOT NULL,
					tg_id BIGINT,
					access jsonb);

CREATE TABLE status_modules (id serial primary key,
							 names varchar(50),
							 description varchar(255),
							 states boolean default False,
							 time_start timestamp default clock_timestamp(),
							 time_end timestamp);

CREATE TABLE conditions_shipments (id serial primary key,
								   conditions varchar(64));

CREATE TABLE details_organization (fsrar_id BIGINT primary key,
									full_name varchar(255) NOT NULL,
					  				inn varchar(30),
					  				kpp varchar(30),
					  				adress text);

CREATE TABLE manufactures ( id BIGINT primary key,
                            reg_number  varchar(40),
                            fix_number  varchar(40),
                            num varchar(128),
                            date_creation date,
                            date_production date,
                            date_fixation date,
                            condition varchar(40),
                            uuid uuid,
                            footing text);

