from typing import Dict

from django.contrib.auth.models import AbstractUser
from django.db import models


def get_default_tg_access() -> Dict[str, int]:
    return {"sms_acc": 0,
            "sms_rej": 0,
            "fix_car": 0,
            "reg_form2": 0,
            "sh_per_day": 0}


def get_label_tg_access() -> Dict[str, str]:
    return {"sms_acc": 'Сообщение о фиксации отгрузки',
            "sms_rej": 'Сообщение о отказе фиксации',
            "fix_car": 'Сообщение о фиксации транспорта',
            "reg_form2": 'Получение информации о продукции отгрузки',
            "sh_per_day": 'Получение информации о отгрузках за дату'}


class Users(AbstractUser):
    tg_id = models.BigIntegerField(null=True, blank=True)
    tg_access = models.JSONField(default=get_default_tg_access)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return f'{self.last_name} {self.first_name}'


class SettingsUsers(models.Model):
    username = models.ForeignKey(Users, on_delete=models.PROTECT)
    order_col_ship_lst = models.JSONField()
    display_col_ship_lst = models.JSONField()

    order_col_client_lst = models.JSONField()
    display_col_client_lst = models.JSONField()

    order_col_product_lst = models.JSONField()
    display_col_product_lst = models.JSONField()

    order_col_manufacture_lst = models.JSONField()
    display_col_manufacture_lst = models.JSONField()


class DetailsOrganization(models.Model):
    fsrar_id = models.BigIntegerField(primary_key=True, )
    full_name = models.CharField(max_length=255)
    inn = models.BigIntegerField(blank=True, null=True)
    kpp = models.BigIntegerField(blank=True, null=True)
    adress = models.TextField(blank=True, null=True)
    loading_place = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'details_organization'
        verbose_name = 'Профиль организации'
        verbose_name_plural = 'Профиль организации'

    def __str__(self) -> str:
        return self.full_name
