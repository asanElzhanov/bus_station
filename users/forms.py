from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    full_name = forms.CharField(label='Полное имя', max_length=150)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.role = User.Role.USER
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'phone')
        labels = {'full_name': 'Полное имя', 'phone': 'Телефон'}
