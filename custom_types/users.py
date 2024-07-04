from typing import TypedDict


class UserAccess(TypedDict):
    fix_car: bool
    sms_acc: bool
    sms_rej: bool
    reg_form2: bool
    sh_per_day: bool


class User(TypedDict):
    name: str
    family: str
    access: UserAccess
