# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/5"
from django.conf.urls import url
from .views import ADCPDataInfoView


urlpatterns = [
    url(r'ADCPInfo/$', ADCPDataInfoView.as_view(), name='adcp_data_info'),
]
