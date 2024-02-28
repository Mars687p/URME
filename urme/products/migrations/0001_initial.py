# Generated by Django 4.2.5 on 2024-01-11 13:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Products',
            fields=[
                ('alcocode', models.BigIntegerField(primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=255)),
                ('capacity', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('alcovolume', models.DecimalField(decimal_places=2, max_digits=10)),
                ('real_alcovolume', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('type_product', models.CharField(max_length=255)),
                ('type_code', models.IntegerField()),
                ('local_reference', models.BooleanField()),
                ('manufacturer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='clients.clients', verbose_name='Производитель')),
            ],
            options={
                'verbose_name': 'Продукт',
                'verbose_name_plural': 'Продукция',
                'db_table': 'products',
                'ordering': ['full_name'],
            },
        ),
    ]
