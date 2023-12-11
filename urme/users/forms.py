from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from users.models import Users, get_label_tg_access

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
    def get_json_dict(self, request):
        user = Users.objects.get(request.user)
        return user.tg_access

    tg_id = forms.IntegerField(widget=forms.TextInput, required=False)
    # for key, value in (get_json_dict()).items():
    #     key = forms.ChoiceField(widget=forms.CheckboxInput(attrs={
    #         'title': label_tg[key]
    #     }), required=False)
    tg_access = forms.JSONField( required=False)

    class Meta:
        model = Users
        fields = ('tg_id', 'tg_access',)


