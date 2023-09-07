DELETE FROM cart_products WHERE form2_new is Null;

DELETE FROM transports WHERE shipment_id in (SELECT id FROM shipments WHERE condition in ('Принято ЕГАИС(без номера фиксации)', 'Отправлено'));

DELETE FROM shipments WHERE condition in ('Принято ЕГАИС(без номера фиксации)', 'Отправлено');