# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/12/3"
from django.conf.urls import url
from .views import StationInfoView, StationAddView, StationModifyView, StationDelView, StationStatusView, StationIndexView, StationSectionView, ShowMapView


urlpatterns = [
    url(r'^info/$', StationInfoView.as_view(), name='station_info'),
    url(r'^stationAdd/$', StationAddView.as_view(), name='station_add'),
    url(r'^stationModify/(?P<station_id>\d+)/$', StationModifyView.as_view(), name='station_modify'),
    url(r'^stationDel/$', StationDelView.as_view(), name='station_del'),
    url(r'^stationStatus/$', StationStatusView.as_view(), name='station_status'),

    url(r'^stationIndex/(?P<station_id>\d+)/$', StationIndexView.as_view(), name='station_index'),
    url(r'^stationSection/(?P<station_id>\d+)/$', StationSectionView.as_view(), name='station_section'),
    url(r'^map/$', ShowMapView.as_view(), name='show_map'),
]
