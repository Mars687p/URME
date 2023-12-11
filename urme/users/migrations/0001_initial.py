# Generated by Django 4.2.5 on 2023-12-08 08:06

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('tg_id', models.BigIntegerField(blank=True, null=True)),
                ('tg_access', models.JSONField(default=users.models.get_default_tg_access)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
                'db_table': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DetailsOrganization',
            fields=[
                ('fsrar_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=255)),
                ('inn', models.BigIntegerField(blank=True, null=True)),
                ('kpp', models.BigIntegerField(blank=True, null=True)),
                ('adress', models.TextField(blank=True, null=True)),
                ('loading_place', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Профиль организации',
                'verbose_name_plural': 'Профиль организации',
                'db_table': 'details_organization',
            },
        ),
        migrations.CreateModel(
            name='SettingsUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_col_ship_lst', models.JSONField()),
                ('display_col_ship_lst', models.JSONField()),
                ('order_col_client_lst', models.JSONField()),
                ('display_col_client_lst', models.JSONField()),
                ('order_col_product_lst', models.JSONField()),
                ('display_col_product_lst', models.JSONField()),
                ('order_col_manufacture_lst', models.JSONField()),
                ('display_col_manufacture_lst', models.JSONField()),
                ('username', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
