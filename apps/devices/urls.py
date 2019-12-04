# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/20"

from django.conf.urls import url
from .views import DevicesInfoView


urlpatterns = [
    url(r'^info/(?P<station_id>\d+)/$', DevicesInfoView.as_view(), name='station_devices'),

]