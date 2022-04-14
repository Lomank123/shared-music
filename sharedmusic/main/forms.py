from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from main.models import Room


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class RoomCreationForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('code', )
