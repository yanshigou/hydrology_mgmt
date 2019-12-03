# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/4"
from django import forms
from users.models import UserProfile, CompanyModel, Message
from rest_framework import serializers


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


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyModel
        fields = ('id', 'company_name', 'contact', 'phone', 'company_status')


class UserProfileSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='get_company_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'mobile', 'permission', 'company_id', 'company_name')


class MessageSerializer(serializers.ModelSerializer):
    time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Message
        fields = '__all__'
