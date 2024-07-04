from clients.models import Clients
from django.db import models
from products.models import Products


class Manufactures(models.Model):
    reg_number = models.CharField(max_length=40, blank=True, null=True)
    fix_number = models.CharField(max_length=40, blank=True, null=True)
    num = models.CharField(max_length=128)
    date_creation = models.DateField('дата создания')
    date_production = models.DateField('дата производства')
    date_fixation = models.DateField('дата фиксации', blank=True, null=True)
    condition = models.CharField('cостояние', max_length=40, choices=(
            ('Отправлено', 'Отправлено'),
            ('Принято ЕГАИС', 'Принято ЕГАИС'),
            ('Отклонено ЕГАИС', 'Отклонено ЕГАИС'),
            ('Зафиксировано в ЕГАИС', 'Зафиксировано в ЕГАИС'),
            ('Распроведено', 'Распроведено')
        ))
    uuid = models.UUIDField()
    type_operation = models.CharField('Тип операции', max_length=40, choices=(
            ('OperProduction', 'Производство'),
            ('OperConversion', 'Переработка'),
            ('OperMaterials', 'Производство сырья для собственного использования')
            ))
    footing = models.TextField('основание', null=True, blank=True)

    class Meta:
        verbose_name = 'Производство'
        verbose_name_plural = 'Производство'
        ordering = ['date_creation']

    def __str__(self) -> str:
        return f'{self.num} | {self.date_creation}'


class ManufacturedProducts(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, verbose_name='продукт')
    manufactures = models.ForeignKey(Manufactures, on_delete=models.PROTECT)
    positions = models.IntegerField('позиция')
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    alcovolume = models.DecimalField('крепость', max_digits=10, decimal_places=4)
    form1 = models.CharField('справка А', max_length=18, blank=True, null=True)
    form2 = models.CharField('справка Б', max_length=18, blank=True, null=True)
    batch_num = models.CharField('номер партии', max_length=128)

    class Meta:
        verbose_name_plural = 'Произведенная продукция'
        indexes = [models.Index(fields=['-manufactures'])]


# Сырье для производства
class RawForManufactured(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, verbose_name='продукт')
    mf_products = models.ForeignKey(ManufacturedProducts, on_delete=models.PROTECT)
    positions = models.IntegerField('позиция')
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    form2 = models.CharField('справка Б', max_length=18)

    class Meta:
        verbose_name_plural = 'Использованное сырье'
        indexes = [models.Index(fields=['-mf_products'])]


class RecieveInfo(models.Model):
    reg_number = models.CharField(max_length=40)
    fix_number = models.CharField(max_length=40)
    num = models.CharField(max_length=128)
    date_creation = models.DateField('дата создания')
    date_fixation = models.DateField('дата фиксации', blank=True, null=True)
    condition = models.CharField('cостояние', max_length=40, choices=(
            ('Отправлено', 'Отправлено'),
            ('Принято ЕГАИС', 'Принято ЕГАИС'),
            ('Получено', 'Получено'),
            ('Отклонено ЕГАИС', 'Отклонено ЕГАИС'),
            ('Зафиксировано в ЕГАИС', 'Зафиксировано в ЕГАИС'),
            ('Проведено', 'Проведено'),
            ('Распроведено', 'Распроведено')
        ))
    uuid = models.UUIDField()
    footing = models.TextField('основание', null=True, blank=True)
    # transport
    change_ownership = models.CharField('право собственности', max_length=30, choices=(
                ('NotChange', 'Не меняется'),
                ('IsChange', 'Меняется')
    ))
    train_company = models.CharField('перевозчик', max_length=255)
    transport_number = models.CharField('номер автомобиля', max_length=50)
    train_trailer = models.CharField('номер прицепа', max_length=50)
    train_customer = models.CharField('заказчик', max_length=255)
    driver = models.CharField('водитель', max_length=255)
    redirection = models.CharField('перенаправление', max_length=255)
    unload_point = models.TextField('место разгрузки')
    dispetcher = models.CharField('экспедитор', max_length=255)
    client = models.ForeignKey(Clients, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Сведение о получении'
        verbose_name_plural = 'Сведения о получении'
        ordering = ['date_creation']

    def __str__(self) -> str:
        return f'{self.num} | {self.date_creation}'


class RecievedProducts(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, verbose_name='продукт')
    receive_info = models.ForeignKey(RecieveInfo, on_delete=models.PROTECT)
    positions = models.IntegerField('позиция')
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    form1 = models.CharField('справка А', max_length=18, blank=True, null=True)
    form2 = models.CharField('справка Б', max_length=18, blank=True, null=True)
    batch_num = models.CharField('номер партии', max_length=128)

    class Meta:
        verbose_name_plural = 'Полученная продукция'
        indexes = [models.Index(fields=['-receive_info'])]


class ImportInfo(models.Model):
    reg_number = models.CharField(max_length=40)
    fix_number = models.CharField(max_length=40)
    num = models.CharField(max_length=128)
    date_creation = models.DateField('дата создания')
    date_report = models.DateField('дата отчета', blank=True, null=True)
    date_td = models.DateField('дата ТД', blank=True, null=True)
    date_fixation = models.DateField('дата фиксации', blank=True, null=True)
    condition = models.CharField('cостояние', max_length=40, choices=(
            ('Отправлено', 'Отправлено'),
            ('Принято ЕГАИС', 'Принято ЕГАИС'),
            ('Получено', 'Получено'),
            ('Отклонено ЕГАИС', 'Отклонено ЕГАИС'),
            ('Зафиксировано в ЕГАИС', 'Зафиксировано в ЕГАИС'),
            ('Проведено', 'Проведено'),
            ('Распроведено', 'Распроведено')
        ))
    uuid = models.UUIDField()
    footing = models.TextField('основание', null=True, blank=True)
    num_td = models.CharField(max_length=128)
    num_contract = models.CharField(max_length=128)
    date_contract = models.DateField('дата контракта')
    from_country = models.CharField(max_length=128)
    receipt_of_imp = models.CharField(max_length=128)
    client = models.ForeignKey(Clients, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Сведение о импорте'
        verbose_name_plural = 'Сведения о импорте'
        ordering = ['date_creation']

    def __str__(self) -> str:
        return f'{self.num} | {self.date_creation}'


class ImportedProducts(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, verbose_name='продукт')
    import_info = models.ForeignKey(RecieveInfo, on_delete=models.PROTECT)
    positions = models.IntegerField('позиция')
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    form1 = models.CharField('справка А', max_length=18, blank=True, null=True)
    form2 = models.CharField('справка Б', max_length=18, blank=True, null=True)
    batch_num = models.CharField('номер партии', max_length=128)

    class Meta:
        verbose_name_plural = 'Импортированная продукция'
        indexes = [models.Index(fields=['-import_info'])]


class ProductResidues(models.Model):
    product = models.ForeignKey(Products, on_delete=models.PROTECT, verbose_name='продукт')
    import_info = models.ForeignKey(RecieveInfo, on_delete=models.PROTECT)
    quantity = models.DecimalField('количество', max_digits=10, decimal_places=4)
    form1 = models.CharField('справка А', max_length=18, blank=True, null=True)
    form2_old = models.CharField('справка Б', max_length=18, blank=True, null=True)
    form2_new = models.CharField('присвоенная справка Б', max_length=18, blank=True, null=True)
    batch_num = models.CharField('номер партии', max_length=128)
    client = models.ForeignKey(Clients, on_delete=models.PROTECT, blank=True, null=True,
                               verbose_name='производитель')

    class Meta:
        verbose_name_plural = 'Остатки'
        indexes = [models.Index(fields=['-product'])]
