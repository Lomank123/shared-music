from django import forms
from main.models import Room, CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "photo")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email",)


class RoomCreationForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ('code', )
