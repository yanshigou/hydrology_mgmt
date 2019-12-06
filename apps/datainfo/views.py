from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse

from .models import ADCPDataInfo, ADCPLevelDataInfo
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
        for i in data_page:
            # TODO 每个时间点多条数据，需计算平均值
            time = i.time
            if time:
                time = datetime.strftime(time, "%Y-%m-%d %H:%M:%S")
            data.append({
                "time": time,
                "speed": i.speed,
                "direction": i.direction,
                "level": ""
            })
        return JsonResponse({
            "draw": draw,
            "recordsTotal": data_infos.count(),
            "recordsFiltered": data_infos.count(),
            "data": data
        })


class DataInfoStationView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            all_station = StationInfo.objects.filter(station_status=True)
        else:
            try:
                company = request.user.company.company_name
                # print(company)
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('index'))
            if company:
                all_station = StationInfo.objects.filter(station_status=True, company__company_name=company)
            else:
                all_station = ""
        create_history_record(request.user, '流量信息查询所有测站点')
        return render(request, 'datainfo_station.html', {
            "all_station": all_station,
        })


class DataInfoView(LoginRequiredMixin, View):
    """
    流量信息展示，汇总各种表数据
    """
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            devices = DevicesInfo.objects.all()
        else:
            company_id = request.user.company.id
            devices = DevicesInfo.objects.filter(station__company_id=company_id, station_id=station_id)
        data_info = list()
        for device in devices:
            data_dict = dict()
            adcp_data_info = ADCPDataInfo.objects.filter(device_id=device.id).last()
            adcp_level_data_info = ADCPLevelDataInfo.objects.filter(device_id=device.id).last()
            data_dict['device'] = device.name
            if adcp_data_info:
                data_dict['time'] = datetime.strftime(adcp_data_info.time, "%Y-%m-%d %H:%M:%S")
                data_dict['speed'] = adcp_data_info.speed
                data_dict['direction'] = adcp_data_info.direction
                data_dict['depth'] = adcp_data_info.depth
                data_dict['distance'] = adcp_data_info.distance
            if adcp_level_data_info:
                data_dict['level'] = adcp_level_data_info.level
                data_dict['power'] = adcp_level_data_info.power
            print(data_dict)
            data_info.append(data_dict)
        print(data_info)
        return render(request, 'data_info.html', {
            # "data_info": data_info,
        })
