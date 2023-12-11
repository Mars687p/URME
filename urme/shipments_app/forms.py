from django import forms
from shipments_app.models import Shipments, CONDITIONS
from users.utils import COLUMNS_SHIPS

PER_DATE = (('today', 'Сегодня'), ('week', 'Неделя'), 
            ('month', 'Месяц'), ('year', 'Год'))
PICK_CONDITIONS = [(0, '')] + [(item, item) for item in CONDITIONS]

class Filter_shipments(forms.Form):
    date_pick = forms.ChoiceField(widget=forms.RadioSelect, 
                                  choices=PER_DATE, required=False)
    date_start = forms.DateField(widget=forms.DateInput(attrs={
                                    'type': 'date',
                                }), required=False)
    number = forms.CharField(widget=forms.TextInput, required=False)
    client = forms.CharField(widget=forms.TextInput, required=False)
    condition = forms.ChoiceField(widget=forms.Select, choices=PICK_CONDITIONS, required=False)

class Pick_display_cl(forms.Form):
    columns = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, 
                                 choices=[i for i in COLUMNS_SHIPS.items() if i[0] != 'id'], required=False)

class Shipments_data(forms.Form):
    num = forms.CharField(widget=forms.TextInput(attrs={
        'readonly': True,

            }))
    condition = forms.CharField(widget=forms.TextInput)
    ttn = forms.CharField(widget=forms.TextInput, required=False)
    fix_number = forms.CharField(widget=forms.TextInput, required=False)
    date_creation = forms.DateField(widget=forms.DateInput(attrs={
                                    'type': 'date',
                                }))
    date_fixation = forms.DateField(widget=forms.DateInput(attrs={
                                    'type': 'date',
                                }), required=False)
    full_name = forms.CharField(widget=forms.TextInput)
    client_id = forms.IntegerField(widget=forms.TextInput)
    
    class meta:
        model = Shipments
        fields = ('num', 'condition', 'ttn', 'fix_number', 'date_creation', 
                  'date_fixation', 'full_name', 'client_id')

