from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import DetailsOrganization, Users

from .forms import CustomUserChangeForm, CustomUserCreationForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = Users
    fieldsets = (
        (None, {'fields': ('username', 'password', 'first_name',
                           'last_name', 'tg_id', 'tg_access', 'last_login',
                           'date_joined',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),)


admin.site.register(Users, CustomUserAdmin)
admin.site.register(DetailsOrganization)
