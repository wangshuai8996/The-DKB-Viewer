from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserLoginForm(forms.Form):
    name = forms.CharField(label='name', max_length=30)
    password = forms.CharField(label='password', max_length=30, widget=forms.PasswordInput)


class CreateUserForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="确认密码")

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super(CreateUserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if confirm_password != password:
            self.add_error('confirm_password', 'Password does not match.')

        return cleaned_data
