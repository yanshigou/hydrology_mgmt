# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/20"

from django.conf.urls import url
from .views import DevicesInfoView, StationDeviceSelectView, DeviceAddView, DeviceModifyView, StationDelView, \
    DeviceStatusView, DeviceDataInfoView

urlpatterns = [
    url(r'^info/(?P<station_id>\d+)/$', DevicesInfoView.as_view(), name='station_devices'),
    url(r'^dataInfo/(?P<device_id>\d+)/$', DeviceDataInfoView.as_view(), name='device_data'),
    url(r'^deviceSelect/$', StationDeviceSelectView.as_view(), name='station_device_select'),
    url(r'^deviceAdd/(?P<station_id>\d+)/$', DeviceAddView.as_view(), name='device_add'),
    url(r'^deviceModify/(?P<station_id>\d+)/(?P<device_id>\d+)/$', DeviceModifyView.as_view(), name='device_modify'),
    url(r'^deviceDel/$', StationDelView.as_view(), name='device_del'),
    url(r'^deviceStatus/$', DeviceStatusView.as_view(), name='device_status'),
]
