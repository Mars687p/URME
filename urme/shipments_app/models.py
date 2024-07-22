from decimal import Decimal

from clients.models import Clients
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from products.models import Products

from app.configuration import get_condition_ships

CONDITIONS = get_condition_ships()
OWNERSHIP = {'NotChange': 'Не меняется',
             'IsChange': 'Меняется'}


class Shipments_query_set(models.QuerySet):
    def ships_per_day(self) -> int:
        date = timezone.now()
        return self.filter(
                            date_creation__year=date.year,
                            date_creation__month=date.month,
                            date_creation__day=date.day).count()

    def ships_per_week(self) -> int:
        date = timezone.now().isocalendar()
        return (self.filter(date_creation__year=date.year,
                            date_creation__week=date.week) & self.exclude(
                                condition=CONDITIONS[3])).count()

    def ships_per_month(self) -> QuerySet:
        date = timezone.now()
        return self.filter(
                date_creation__year=date.year,
                date_creation__month=date.month).exclude(condition=CONDITIONS[3])

    def ships_per_year(self) -> QuerySet:
        date = timezone.now()
        return self.filter(date_creation__year=date.year,).exclude(
                            condition=CONDITIONS[3])

    def get_unique_clients(self) -> int:
        return self.values('client_id').order_by('client_id').distinct('client_id').count()

    def active_ships(self) -> int:
        return self.filter(condition__in=CONDITIONS[:2]).count()

    def output_list(self, order_cl: dict, isdisplay: dict) -> QuerySet:
        query = self.values(*(field for field in order_cl.keys() if isdisplay[field]))
        for item in query:
            try:
                item['num'] = str(item['num']).rjust(6, '0')
                item['client__fsrar_id'] = str(item['client__fsrar_id']).rjust(12, '0')
            except KeyError:
                pass
        return query


class Shipments(models.Model):
    num = models.CharField('номер', max_length=128)
    condition = models.CharField('cостояние', max_length=40, choices=(
            ('Отправлено', 'Отправлено'),
            ('Принято ЕГАИС(без номера фиксации)', 'Принято ЕГАИС(без номера фиксации)'),
            ('Принято ЕГАИС', 'Принято ЕГАИС'),
            ('Отклонено ЕГАИС', 'Отклонено ЕГАИС'),
            ('Проведено', 'Проведено'),
            ('Проведено Частично', 'Проведено Частично'),
            ('Распроведено', 'Распроведено')
        ))
    uuid = models.UUIDField(blank=True, null=True)
    ttn = models.CharField('TTN-номер', max_length=50, blank=True, null=True)
    fix_number = models.CharField('FIX-номер', max_length=50, blank=True, null=True)
    date_creation = models.DateField('дата создания')
    date_fixation = models.DateField('дата фиксации', blank=True, null=True)
    client = models.ForeignKey(Clients, on_delete=models.PROTECT, verbose_name="клиент")
    footing = models.TextField('основание', null=True, blank=True)

    objects = Shipments_query_set.as_manager()

    class Meta:
        db_table = 'shipments'
        verbose_name = 'Отгрузка'
        verbose_name_plural = 'Отгрузки'
        ordering = ['-date_creation', '-num']
        indexes = [models.Index(fields=['-date_creation'])]

    def __str__(self) -> str:
        return str(self.num).rjust(6, '0')

    def get_absolute_url(self) -> str:
        return reverse('shipments_app:shipment', args=[self.id])

    def get_format_num(self) -> str:
        return str(self.num).rjust(6, '0')

    def get_values_form(self) -> dict:
        return {'num': self.get_format_num(), 'condition': self.condition, 'ttn': self.ttn,
                'fix_number': self.fix_number, 'date_creation': self.date_creation,
                'date_fixation': self.date_fixation, 'full_name': self.client.full_name,
                'client_id': str(self.client.fsrar_id).rjust(12, '0')}


class Transports(models.Model):
    shipment = models.ForeignKey(Shipments, on_delete=models.PROTECT, blank=True, null=True)
    change_ownership = models.CharField('право собственности', max_length=30, blank=True,
                                        null=True, choices=(
                                                    ('NotChange', 'Не меняется'),
                                                    ('IsChange', 'Меняется')
                                                ))
    train_company = models.CharField('перевозчик', max_length=255, blank=True, null=True)
    transport_number = models.CharField('номер автомобиля', max_length=50, blank=True, null=True)
    train_trailer = models.CharField('номер прицепа', max_length=50, blank=True, null=True)
    train_customer = models.CharField('заказчик', max_length=255, blank=True, null=True)
    driver = models.CharField('водитель', max_length=255, blank=True, null=True)
    unload_point = models.TextField('место разгрузки', blank=True, null=True)

    class Meta:
        db_table = 'transports'
        verbose_name_plural = 'Transports'
        indexes = [models.Index(fields=['-transport_number'])]

    def __str__(self) -> str:
        return self.transport_number

    def get_values_form(self) -> dict:
        return {'change_ownership': OWNERSHIP[self.change_ownership],
                'train_company': self.train_company,
                'transport_number': self.transport_number,
                'train_trailer': self.train_trailer,
                'train_customer': self.train_customer,
                'driver': self.driver,
                'unload_point': self.unload_point}


class CartProducts(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, blank=True, null=True,
                                verbose_name='продукт')
    shipment = models.ForeignKey(Shipments, on_delete=models.PROTECT, blank=True, null=True)
    positions = models.CharField('позиция', max_length=3)
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    price_for_one = models.DecimalField('цена за шт.', max_digits=10, decimal_places=4)
    bottling_date = models.DateField('дата розлива', blank=True, null=True)
    form1 = models.CharField('справка А', max_length=18, blank=True, null=True)
    form2_old = models.CharField('справка Б', max_length=18)
    form2_new = models.CharField('присвоенная справка Б', max_length=18, blank=True, null=True)

    class Meta:
        db_table = 'cart_products'
        verbose_name_plural = 'Cart_Products'

    def get_volume_dal(self) -> Decimal:
        if self.product.capacity is None:
            return self.quantity.quantize(Decimal('1.00000'))
        return Decimal((self.quantity * self.product.capacity)/10).quantize(Decimal('1.00000'))

    def get_abs_volume(self) -> Decimal:
        return Decimal(self.get_volume_dal() *
                       Decimal(self.product.alcovolume/100)).quantize(Decimal('1.00000'))

    def get_price_position(self) -> Decimal:
        return Decimal(self.quantity * self.price_for_one).quantize(Decimal('1.0000'))

    def get_alcocode(self) -> str:
        return str(self.product.alcocode).rjust(19, "0")
