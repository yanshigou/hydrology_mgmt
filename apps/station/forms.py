# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/3"
from django import forms
from .models import StationInfo
from rest_framework import serializers


class StationInfoForm(forms.ModelForm):
    class Meta:
        model = StationInfo
        fields = ["station_name", "station_code", "river", "longitude", "latitude", "station_address", "company"]


class StationStatusForm(forms.ModelForm):
    class Meta:
        model = StationInfo
        fields = ['station_status']
