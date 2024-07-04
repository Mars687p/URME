from typing import Optional, TypedDict


class Counterparty(TypedDict):
    fsrar_id: Optional[int]
    name: Optional[str]
    address: Optional[str]
    INN: Optional[int]
    KPP: Optional[int]
