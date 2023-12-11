from django import forms
from users.utils import COLUMNS_CLIENTS


class Filter_clients(forms.Form):
    fsrar_id = forms.IntegerField(widget=forms.TextInput, required=False)
    client = forms.CharField(widget=forms.TextInput, required=False)
    inn = forms.IntegerField(widget=forms.TextInput, required=False)
    kpp = forms.IntegerField(widget=forms.TextInput, required=False)

class Pick_display_cl_clients(forms.Form):
    columns = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, 
                    choices=[i for i in COLUMNS_CLIENTS.items() if i[0] != 'fsrar_id'], required=False)

class Select_date(forms.Form):
    date_select = forms.ChoiceField(widget=forms.RadioSelect(attrs={'onchange': 'listen_select(value)'}), 
                                    choices=(('month', 'Месяц'), 
                                             ('year', 'Год')), required=False
                                    )