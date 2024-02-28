from django.db import models
from clients.models import Clients 

class Products_query_set(models.QuerySet):
    def output_list(self, order_cl, isdisplay) -> dict:
        query = self.values(*(field for field in order_cl.keys() if isdisplay[field]))
        for item in query:
            try:
                item['alcocode'] = str(item['alcocode']).rjust(19, '0')
            except KeyError:
                pass
        return query
    
    def get_unique_alcovolume(self) -> tuple:
        alcovolume = self.values('alcovolume').order_by('alcovolume').distinct('alcovolume')
        return (i['alcovolume'] for i in alcovolume)

    def get_unique_capacity(self) -> tuple:
        capacity = self.values('capacity').order_by('capacity').distinct('capacity')
        return (i['capacity'] for i in capacity)

    def get_unique_type_code(self) -> tuple:
        type_code = self.values('type_code').order_by('type_code').distinct('type_code')
        return (i['type_code'] for i in type_code)



class Products(models.Model):
    alcocode = models.BigIntegerField(primary_key=True)
    full_name = models.CharField(max_length=255)
    capacity = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=4)
    alcovolume = models.DecimalField(max_digits=10, decimal_places=2)
    real_alcovolume = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    type_product = models.CharField(max_length=255)
    type_code = models.IntegerField()
    local_reference = models.BooleanField()
    manufacturer = models.ForeignKey(Clients, on_delete=models.DO_NOTHING, blank=True, null=True, verbose_name='Производитель')


    objects = Products_query_set.as_manager()

    class Meta:
        db_table = 'products'
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукция'
        ordering = ['full_name']

    def __str__(self) -> str:
        return self.full_name
    
    def get_format_alcocode(self):
        return str(self.alcocode).rjust(19, '0')
