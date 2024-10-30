from django import forms
from django.contrib.auth.forms import (AuthenticationForm, UserChangeForm,
                                       UserCreationForm)
from django.http import HttpRequest
from users.models import Users, get_label_tg_access

from custom_types.users import UserAccess

label_tg = get_label_tg_access()


class Users_login_form(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input-form-username',
        'placeholder': 'Логин',
        'id': 'for_label_err'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'input-form-password',
        'placeholder': 'Пароль'
    }))

    class Meta:
        model = Users
        fields = ('username', 'password')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Users
        fields = ('tg_id', 'tg_access',)


class CustomUserChangeForm(UserChangeForm):
    def get_json_dict(self, request: HttpRequest) -> UserAccess:
        user = Users.objects.get(request.user)
        return user.tg_access

    tg_id = forms.IntegerField(widget=forms.TextInput, required=False)
    tg_access = forms.JSONField(
        required=False,
        help_text="""
            "fix_car": Отправлять оповещение о фиксации машины
            "sms_acc": Отправлять оповещение о фиксации отгрузки
            "sms_rej": Отправлять оповещение о отклонении отгрузки
            "reg_form2": Добавлять кнопку для возможности просмотра подробно информации об отгрузке
            "sh_per_day": Добавлять кнопку для возможности просмотра отгрузок за дату""")

    class Meta:
        model = Users
        fields = ('tg_id', 'tg_access',)
