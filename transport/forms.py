from django import forms
from .models import Transport


class TransportForm(forms.ModelForm):
    class Meta:
        model = Transport
        fields = ('name',)
        labels = {'name': 'Название транспорта'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Например: Автобус МАЗ-206'}),
        }
