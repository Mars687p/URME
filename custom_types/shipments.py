from typing import Literal, TypedDict


class Ships(TypedDict):
    num: int
    condition: Literal['Отправлено', 'Принято ЕГАИС(без номера фиксации)',
                       'Принято ЕГАИС', 'Отклонено ЕГАИС', 'Проведено',
                       'Проведено Частично', 'Распроведено']
    client_id: int
    cl_name: str
    ttn: str
    fix_number: str
    date_create: str


class ShipsWithTransport(Ships):
    train_company: str
    transport_number: str
    train_trailer: str
    driver: str
