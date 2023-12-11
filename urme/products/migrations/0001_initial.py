# Generated by Django 4.2.5 on 2023-12-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Products',
            fields=[
                ('alcocode', models.BigIntegerField(primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=255)),
                ('capacity', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('alcovolume', models.DecimalField(decimal_places=2, max_digits=10)),
                ('type_product', models.CharField(max_length=255)),
                ('type_code', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Products',
                'db_table': 'products',
                'ordering': ['full_name'],
            },
        ),
    ]
