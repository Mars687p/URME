# Generated by Django 4.2.5 on 2023-12-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Clients',
            fields=[
                ('fsrar_id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name='FSRAR ID получателя')),
                ('full_name', models.CharField(max_length=255, verbose_name='клиент')),
                ('inn', models.BigIntegerField(blank=True, null=True, verbose_name='ИНН')),
                ('kpp', models.BigIntegerField(blank=True, null=True, verbose_name='КПП')),
                ('adress', models.TextField(blank=True, null=True, verbose_name='адрес')),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': 'Клиенты',
                'db_table': 'clients',
                'ordering': ['full_name', 'fsrar_id'],
                'indexes': [models.Index(fields=['full_name'], name='clients_full_na_86b218_idx')],
            },
        ),
    ]