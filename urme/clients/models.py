from django.db import models


class Clients_query_set(models.QuerySet):
    def output_list(self, order_cl: dict, isdisplay: dict) -> dict:
        query = self.values(*(field for field in order_cl.keys() if isdisplay[field]))
        for item in query:
            try:
                item['fsrar_id'] = str(item['fsrar_id']).rjust(12, '0')
            except KeyError:
                pass
        return query


class Clients(models.Model):
    fsrar_id = models.BigIntegerField('FSRAR ID получателя', primary_key=True)
    full_name = models.CharField('клиент', max_length=255)
    inn = models.BigIntegerField('ИНН', blank=True, null=True)
    kpp = models.BigIntegerField('КПП', blank=True, null=True)
    adress = models.TextField('адрес', blank=True, null=True)

    objects = Clients_query_set.as_manager()

    class Meta:
        db_table = 'clients'
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['full_name', 'fsrar_id']
        indexes = [models.Index(fields=['full_name'])]

    def __str__(self) -> str:
        return f"{str(self.fsrar_id).rjust(12, '0')}: {self.full_name}"

    def get_format_id(self) -> str:
        return str(self.fsrar_id).rjust(12, '0')
