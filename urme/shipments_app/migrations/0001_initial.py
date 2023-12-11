# Generated by Django 4.2.5 on 2023-12-08 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField(verbose_name='номер')),
                ('condition', models.CharField(choices=[('Отправлено', 'Отправлено'), ('Принято ЕГАИС(без номера фиксации)', 'Принято ЕГАИС(без номера фиксации)'), ('Принято ЕГАИС', 'Принято ЕГАИС'), ('Отклонено ЕГАИС', 'Отклонено ЕГАИС'), ('Проведено', 'Проведено'), ('Проведено Частично', 'Проведено Частично'), ('Распроведено', 'Распроведено')], max_length=40, verbose_name='cостояние')),
                ('uuid', models.UUIDField(blank=True, null=True)),
                ('ttn', models.CharField(blank=True, max_length=50, null=True, verbose_name='TTN-номер')),
                ('fix_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='FIX-номер')),
                ('date_creation', models.DateField(verbose_name='дата создания')),
                ('date_fixation', models.DateField(blank=True, null=True, verbose_name='дата фиксации')),
                ('footing', models.TextField(blank=True, null=True, verbose_name='основание')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='clients.clients', verbose_name='клиент')),
            ],
            options={
                'verbose_name': 'Отгрузка',
                'verbose_name_plural': 'Отгрузки',
                'db_table': 'shipments',
                'ordering': ['-date_creation', '-num'],
            },
        ),
        migrations.CreateModel(
            name='CartProducts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('positions', models.CharField(max_length=3, verbose_name='позиция')),
                ('quantity', models.BigIntegerField(verbose_name='количество')),
                ('price_for_one', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='цена за шт.')),
                ('form2_old', models.CharField(max_length=18, verbose_name='справка Б')),
                ('form2_new', models.CharField(blank=True, max_length=18, null=True, verbose_name='присвоенная справка Б')),
                ('form1', models.CharField(blank=True, max_length=18, null=True, verbose_name='справка А')),
                ('bottling_date', models.DateField(blank=True, null=True, verbose_name='дата розлива')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='products.products', verbose_name='продукт')),
                ('shipment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shipments_app.shipments')),
            ],
            options={
                'verbose_name_plural': 'Cart_Products',
                'db_table': 'cart_products',
            },
        ),
        migrations.CreateModel(
            name='Transports',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_ownership', models.CharField(blank=True, choices=[('NotChange', 'Не меняется'), ('IsChange', 'Меняется')], max_length=30, null=True, verbose_name='право собственности')),
                ('train_company', models.CharField(blank=True, max_length=255, null=True, verbose_name='перевозчик')),
                ('transport_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='номер автомобиля')),
                ('train_trailer', models.CharField(blank=True, max_length=50, null=True, verbose_name='номер прицепа')),
                ('train_customer', models.CharField(blank=True, max_length=255, null=True, verbose_name='заказчик')),
                ('driver', models.CharField(blank=True, max_length=255, null=True, verbose_name='водитель')),
                ('unload_point', models.TextField(blank=True, null=True, verbose_name='место разгрузки')),
                ('shipment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shipments_app.shipments')),
            ],
            options={
                'verbose_name_plural': 'Transports',
                'db_table': 'transports',
                'indexes': [models.Index(fields=['-transport_number'], name='transports_transpo_6837e0_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='shipments',
            index=models.Index(fields=['-date_creation'], name='shipments_date_cr_3a219c_idx'),
        ),
    ]
