from django import forms
from .models import Route, Stop


class RouteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields['booking_max_days'].initial = 7

    class Meta:
        model  = Route
        fields = ('name', 'transport', 'departure_time', 'booking_max_days')
        labels = {
            'name': 'Название маршрута',
            'transport': 'Транспорт',
            'departure_time': 'Время отправления',
            'booking_max_days': 'Максимум дней для продажи',
        }
        widgets = {
            'departure_time': forms.TimeInput(attrs={'type': 'time'}),
            'name': forms.TextInput(attrs={'placeholder': 'Астана — Алматы'}),
            'booking_max_days': forms.NumberInput(attrs={'min': 1}),
        }


class StopForm(forms.ModelForm):
    class Meta:
        model  = Stop
        fields = ('city', 'order', 'price_from_start', 'arrival_time', 'departure_time',
                  'is_boarding_allowed', 'is_alighting_allowed')
        labels = {
            'city':                  'Город',
            'order':                 'Порядок',
            'price_from_start':      'Цена от начала (тг)',
            'arrival_time':          'Время прибытия',
            'departure_time':        'Время отправления',
            'is_boarding_allowed':   'Посадка',
            'is_alighting_allowed':  'Высадка',
        }
        widgets = {
            'city':                  forms.TextInput(attrs={'placeholder': 'Астана'}),
            'order':                 forms.NumberInput(attrs={'min': 0}),
            'price_from_start':      forms.NumberInput(attrs={'min': 0}),
            'arrival_time':          forms.TimeInput(attrs={'type': 'time'}),
            'departure_time':        forms.TimeInput(attrs={'type': 'time'}),
        }
