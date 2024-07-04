from datetime import date
from typing import Optional, TypedDict


class BaseFixation(TypedDict):
    fix_date: date


class FixationShipments(BaseFixation):
    ttn: Optional[str]
    fix_number: Optional[str]


class FixationManufactures(BaseFixation):
    RegID: str
