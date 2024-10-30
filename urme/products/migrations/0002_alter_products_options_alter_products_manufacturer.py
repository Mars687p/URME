# Generated by Django 4.2.5 on 2024-07-17 10:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='products',
            options={'ordering': ['-local_reference', '-alcocode'], 'verbose_name': 'Продукт', 'verbose_name_plural': 'Продукция'},
        ),
        migrations.AlterField(
            model_name='products',
            name='manufacturer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.clients', verbose_name='Производитель'),
        ),
    ]