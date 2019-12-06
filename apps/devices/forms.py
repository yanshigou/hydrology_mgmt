# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/6"
from django import forms
from .models import DevicesInfo


class DevicesInfoForm(forms.ModelForm):
    class Meta:
        model = DevicesInfo
        fields = ["device_id", "station", "name", "device_type", "install_method", "fs_direction", "start_point",
                  "offset", "longitude", "latitude"]


class DevicesStatusForm(forms.ModelForm):
    class Meta:
        model = DevicesInfo
        fields = ['device_status']
