from django import forms
from django.db.utils import ProgrammingError
from .models import Products
from users.utils import COLUMNS_PRODUCTS


class Filter_products(forms.Form):
    alcocode = forms.IntegerField(widget=forms.TextInput, required=False)
    full_name = forms.CharField(widget=forms.TextInput, required=False)
    try:
        capacity = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                            choices=((i, i) for i in
                                    Products.objects.get_unique_capacity()), required=False)
        alcovolume = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                            choices=((i, i) for i in
                                    Products.objects.get_unique_alcovolume()), required=False)
        type_product = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                choices=(('АП', 'АП'),
                                                        ('ССПП', 'ССПП'),
                                                        ('ЭС', 'ЭС'),
                                                        ), required=False)
        type_code = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                            choices=((i, i) for i in
                                        Products.objects.get_unique_type_code()), required=False)
    except ProgrammingError:
        pass

class Pick_display_cl_products(forms.Form):
    columns = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, 
                    choices=[i for i in COLUMNS_PRODUCTS.items() if i[0] != 'alcocode'], required=False)
    