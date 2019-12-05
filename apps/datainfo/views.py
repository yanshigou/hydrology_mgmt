from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse

from .models import ADCPDataInfo
from devices.models import DevicesInfo
from station.models import StationInfo
from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta


class ADCPDataInfoView(LoginRequiredMixin, View):
    def get(self, request):
        end_time = datetime.now()
        start_time = end_time + timedelta(days=-3)
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            devices = DevicesInfo.objects.all()
            stations = StationInfo.objects.all()
            return render(request, 'adcp_paginator.html', {
                "start_time": start_time,
                "end_time": end_time,
                "devices": devices,
                "stations": stations
            })
        else:
            company_id = request.user.company.id
            devices = DevicesInfo.objects.filter(station__company_id=company_id)
            stations = StationInfo.objects.filter(company_id=company_id)
            create_history_record(request.user, "查询水量数据")
            return render(request, 'adcp_paginator.html', {
                "start_time": start_time,
                "end_time": end_time,
                "devices": devices,
                "stations": stations
            })

    def post(self, request):
        start_time = request.POST.get('start_time', '')
        end_time = request.POST.get('end_time', '')
        device_id = request.POST.get('device_id')
        station_id = request.POST.get('station_id')

        draw = request.POST.get('draw', "1")
        start = request.POST.get('start', "0")
        length = request.POST.get('length', "10")
        page = request.POST.get('page', "1")
        print(draw, start, length, page)
        if device_id == "0":
            # TODO 计算断面平均，所有设备数据平均
            data_infos = ADCPDataInfo.objects.filter(time__gte=start_time, time__lte=end_time,
                                                     device__station=station_id).order_by('-time')
        else:
            data_infos = ADCPDataInfo.objects.filter(device_id=device_id, time__gte=start_time, time__lte=end_time,
                                                     device__station=station_id).order_by('-time')
        print(data_infos.values())
        page2 = request.POST.get('page', '1')
        # print(len(all_wt_data))
        paginator = Paginator(data_infos, length)
        try:
            data_page = paginator.page(page2)
        except PageNotAnInteger:
            data_page = paginator.page(1)
        except EmptyPage:
            data_page = paginator.page(paginator.num_pages)
        print(data_page)
        data = []
        # for i in data_page:
        #     # TODO 每个时间点多条数据，需计算平均值
        #     print(i.time)
        #     print(i.speed)
        #     print(i.direction)
        #     # data.append({
        #     # })
        return JsonResponse({
            "draw": draw,
            "recordsTotal": data_infos.count(),
            "recordsFiltered": data_infos.count(),
            "data": data
        })
