--NOTIFY/LISTEN for shipments
CREATE OR REPLACE FUNCTION ships_insert_or_update() RETURNS TRIGGER AS $$
BEGIN 
	PERFORM(
		WITH payload("id", "num", "condition", "uuid", "ttn", "fix_number", "date_creation", 
					 "client_id", "cl_full_name")
			AS (SELECT NEW.id, NEW.num, NEW.condition, NEW.uuid, NEW.ttn, NEW.fix_number, 
				NEW.date_creation, NEW.client_id, clients.full_name FROM shipments as sh 
				RIGHT JOIN clients ON clients.fsrar_id = sh.client_id
			    WHERE NEW.id = sh.id)
		SELECT pg_notify('ships_insert_or_update', row_to_json(payload) :: TEXT)
		FROM payload
		);
	RETURN NULL;
END
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE TRIGGER ships_ins_or_upd_trig
AFTER INSERT OR UPDATE ON shipments
FOR EACH ROW EXECUTE FUNCTION ships_insert_or_update();

--transports insert
CREATE OR REPLACE FUNCTION tr_insert() RETURNS TRIGGER AS $$
BEGIN 
	PERFORM(
		WITH payload("sh_id", "change_ownership", "company", "tr_num", "trailer", 
					 "customer", "driver", "unload_point")
			AS (SELECT NEW.shipment_id, NEW.change_ownership, NEW.train_company, 
				NEW.transport_number, NEW.train_trailer, NEW.train_customer, NEW.driver, 
				NEW.unload_point FROM transports WHERE shipment_id = NEW.shipment_id)
		SELECT pg_notify('tr_insert', row_to_json(payload) :: TEXT)
		FROM payload
		);
	RETURN NULL;
END
$$ LANGUAGE 'plpgsql';

CREATE OR REPLACE TRIGGER tr_insert_trig
AFTER INSERT ON transports
FOR EACH ROW EXECUTE PROCEDURE tr_insert();

INSERT INTO status_modules(names, description) 
VALUES ('utm_queue', 'Модуль работы с очередью УТМ'), 
		('parsing_shipments', 'Модуль парсинга документов'), 
		('tg_bot', 'Телеграм-бот');



INSERT INTO conditions_shipments (conditions)
VALUES ('Отправлено'), ('Принято ЕГАИС(без номера фиксации)'), 
	   ('Принято ЕГАИС'), ('Отклонено ЕГАИС'), ('Проведено'), 
	   ('Проведено Частично'), ('Распроведено');

INSERT INTO details_organization (fsrar_id,	full_name, inn, kpp, adress)
VALUES (010000000444, 'Открытое акционерное общество Агрофирма "Жемчужина Ставрополья"', 2624022986, 
		262401001, 'ОАО АФ "Жемчужина Ставрополья"Россия, 356826, Ставропольский край, Буденновский район, с.Красный Октябрь, ул.Победы,9');

CREATE USER tg_bot WITH PASSWORD 'myPassword';
GRANT SELECT (id, names, family, tg_access) ON users to tg_bot;
GRANT SELECT  ON shipments, transports, products, cart_products, clients to tg_bot;
GRANT SELECT, UPDATE (states, time_start, time_end) ON status_modules TO tg_bot;

CREATE USER dj_user WITH PASSWORD 'myPassword';
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "dj_user";



