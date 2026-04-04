from django import forms
from routes.models import Stop


class BookingForm(forms.Form):
    from_stop = forms.ModelChoiceField(
        queryset=Stop.objects.none(),
        label='Откуда садитесь'
    )
    to_stop = forms.ModelChoiceField(
        queryset=Stop.objects.none(),
        label='Где выходите'
    )
    customer_name = forms.CharField(
        label='Ваше имя', max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Иван Иванов'})
    )
    phone = forms.CharField(
        label='Телефон', max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+7 777 123 45 67'})
    )
    extra_info = forms.CharField(
        label='Доп. информация', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Багаж, пожелания...'})
    )
    travel_date = forms.DateField(widget=forms.HiddenInput)

    def __init__(self, *args, route=None, **kwargs):
        super().__init__(*args, **kwargs)
        if route:
            # Только остановки с разрешённой посадкой
            self.fields['from_stop'].queryset = Stop.objects.filter(
                route=route, is_boarding_allowed=True
            ).order_by('order')
            # Только остановки с разрешённой высадкой
            self.fields['to_stop'].queryset = Stop.objects.filter(
                route=route, is_alighting_allowed=True
            ).order_by('order')

    def clean(self):
        cleaned   = super().clean()
        from_stop = cleaned.get('from_stop')
        to_stop   = cleaned.get('to_stop')
        if from_stop and to_stop:
            if from_stop.order >= to_stop.order:
                raise forms.ValidationError(
                    'Остановка посадки должна быть раньше остановки высадки.'
                )
        return cleaned
