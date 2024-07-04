from datetime import date
from decimal import Decimal
from typing import Dict, Optional, TypedDict

from custom_types.counterparty import Counterparty


class BaseProduct(TypedDict):
    alcocode: int
    alcovolume: Decimal


class Product(BaseProduct):
    name: str
    type_code: int
    type_product: str


class RawProductManufactures(BaseProduct):
    form2: str
    quantity: Decimal


class ProductManufactures(BaseProduct):
    quantity: Optional[Decimal]
    party: Optional[str]
    form1: Optional[str]
    form2: Optional[str]
    raw: Dict[int, RawProductManufactures]


class ProductShipments(Product):
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    form2_old: Optional[str]
    form1: Optional[str]
    capacity: Optional[Decimal]
    form2_new: Optional[str]
    bottling_date: Optional[date]


class ProductReference(Product):
    capacity: Optional[Decimal]
    manufacturer: Counterparty
