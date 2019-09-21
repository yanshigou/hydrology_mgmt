# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/20"
from django import forms
from users.models import UserProfile


class RegisterForm(forms.Form):
    username = forms.CharField(required=True)
    password1 = forms.CharField(required=True, min_length=6)
    password2 = forms.CharField(required=True, min_length=6)


class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, min_length=6)


class PasswordForm(forms.Form):
    old_password = forms.CharField(required=True, min_length=6)
    password1 = forms.CharField(required=True, min_length=6)
    password2 = forms.CharField(required=True, min_length=6)


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['image']


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'gender', 'company', 'unique_id', 'mobile']

