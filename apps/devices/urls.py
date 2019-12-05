# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/20"

from django.conf.urls import url
from .views import DevicesInfoView, StationDeviceSelectView, DeviceAddView


urlpatterns = [
    url(r'^info/(?P<station_id>\d+)/$', DevicesInfoView.as_view(), name='station_devices'),
    url(r'^deviceSelect/$', StationDeviceSelectView.as_view(), name='station_device_select'),
    url(r'^deviceAdd/(?P<station_id>\d+)/$', DeviceAddView.as_view(), name='device_add'),

]