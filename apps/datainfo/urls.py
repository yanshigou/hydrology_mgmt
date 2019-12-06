# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/5"
from django.conf.urls import url
from .views import ADCPDataInfoView, DataInfoStationView, DataInfoView


urlpatterns = [
    url(r'ADCPInfo/$', ADCPDataInfoView.as_view(), name='adcp_data_info'),
    url(r'dataInfoStation/$', DataInfoStationView.as_view(), name='data_info_station'),
    url(r'dataInfo/(?P<station_id>\d+)/$', DataInfoView.as_view(), name='data_info'),
]
