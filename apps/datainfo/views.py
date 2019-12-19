from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.db import connection
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
            return render(request, 'adcp_paginator2.html', {
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
            return render(request, 'adcp_paginator2.html', {
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
        print(device_id)
        data_list = []
        if device_id == "0":
            # TODO 计算断面平均，所有设备数据平均
            sql = "SELECT adcpinfo.time, AVG(adcpinfo.speed) as avg_speed, AVG(adcpinfo.direction) as avg_direction " \
                  "from (SELECT datainfo_adcpdatainfo.time, datainfo_adcpdatainfo.speed, datainfo_adcpdatainfo.depth, " \
                  "datainfo_adcpdatainfo.direction, datainfo_adcpdatainfo.distance FROM datainfo_adcpdatainfo " \
                  "WHERE  datainfo_adcpdatainfo.time >= \'{start_time}\' " \
                  "AND datainfo_adcpdatainfo.time <= \'{end_time}\' ) adcpinfo  " \
                  "RIGHT JOIN (SELECT station_id FROM devices_devicesinfo) deviceinfo on " \
                  "deviceinfo.station_id=\'{station_id}\'" \
                  "GROUP BY adcpinfo.time ORDER BY adcpinfo.time"
            with connection.cursor() as cursor:
                # print(sql.format(device_id=device_id, start_time=start_time, end_time=end_time, station_id=station_id))
                cursor.execute(sql.format(device_id=device_id, start_time=start_time, end_time=end_time, station_id=station_id))
                all_data = cursor.fetchall()
                # print(all_data)
                for data in all_data:
                    time, avg_speed, avg_direction = data
                    if time and avg_speed and avg_direction:
                        # print(time, avg_speed, avg_direction)
                        level_data = ADCPLevelDataInfo.objects.order_by('time')
                        level_data2 = level_data.filter(
                            time__range=(time + timedelta(minutes=-10), time + timedelta(minutes=10))).last()
                        if level_data2:
                            level = level_data2.level
                        elif not level_data2 and level_data:
                            level = level_data.last().level
                        else:
                            level = ""
                        # print(level)
                        data_list.append({
                            "time": datetime.strftime(time, "%Y-%m-%d %H:%M:%S"),
                            "flow": "未算",
                            "area": "未算",
                            "avg_speed": "%.2f" % avg_speed,
                            "avg_direction": "%.2f" % avg_direction,
                            "level": level
                        })
            # print(data_list)
        else:
            sql = "SELECT adcpinfo.time, AVG(adcpinfo.speed) as avg_speed, AVG(adcpinfo.direction) as avg_direction " \
                  "from (SELECT datainfo_adcpdatainfo.time, datainfo_adcpdatainfo.speed, datainfo_adcpdatainfo.depth, " \
                  "datainfo_adcpdatainfo.direction, datainfo_adcpdatainfo.distance FROM datainfo_adcpdatainfo " \
                  "WHERE device_id=\'{device_id}\' AND datainfo_adcpdatainfo.time >= \'{start_time}\' " \
                  "AND datainfo_adcpdatainfo.time <= \'{end_time}\' ) adcpinfo  " \
                  "RIGHT JOIN (SELECT station_id FROM devices_devicesinfo) deviceinfo on " \
                  "deviceinfo.station_id=\'{station_id}\'" \
                  "GROUP BY adcpinfo.time ORDER BY adcpinfo.time"
            with connection.cursor() as cursor:
                cursor.execute(sql.format(device_id=device_id, start_time=start_time, end_time=end_time, station_id=station_id))
                all_data = cursor.fetchall()
                # print(all_data)
                for data in all_data:
                    time, avg_speed, avg_direction = data
                    if time and avg_speed and avg_direction:
                        level_data = ADCPLevelDataInfo.objects.filter(device_id=device_id).order_by('time')
                        level_data2 = level_data.filter(time__range=(time + timedelta(minutes=-10), time + timedelta(minutes=10))).last()
                        if level_data2:
                            level = level_data2.level
                        elif not level_data2 and level_data:
                            level = level_data.last().level
                        else:
                            level = ""
                        # print(level)
                        data_list.append({
                            "time": datetime.strftime(time, "%Y-%m-%d %H:%M:%S"),
                            "flow": "",
                            "area": "",
                            "avg_speed": "%.2f" % avg_speed,
                            "avg_direction": "%.2f" % avg_direction,
                            "level": level
                        })
            # print(data_list)
        page2 = request.POST.get('page', '1')
        # print(len(all_wt_data))
        paginator = Paginator(data_list, length)
        try:
            data_page = paginator.page(page2)
        except PageNotAnInteger:
            data_page = paginator.page(1)
        except EmptyPage:
            data_page = paginator.page(paginator.num_pages)
        print(data_page)

        return JsonResponse({
            "draw": draw,
            "recordsTotal": len(data_list),
            "recordsFiltered": len(data_list),
            "data": data_list
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
    # TODO 断面平均计算 流量水位图的数据
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            devices = DevicesInfo.objects.filter(station_id=station_id)
        else:
            company_id = request.user.company.id
            devices = DevicesInfo.objects.filter(station__company_id=company_id, station_id=station_id)
        data_info = list()
        station_name = StationInfo.objects.get(id=station_id).station_name
        for device in devices:
            data_dict = dict()
            adcp_data_info = ADCPDataInfo.objects.filter(device_id=device.id).last()
            data_dict['device'] = device.name
            data_dict['id'] = device.id
            if adcp_data_info:
                a_last_time = adcp_data_info.time
                adcp_data_info = ADCPDataInfo.objects.filter(device_id=device.id, time=a_last_time)
                speed_list = list()
                direction_list = list()
                for data in adcp_data_info:
                    speed_list.append(float(data.speed))
                    direction_list.append(float(data.direction))
                avg_speed = "%.2f" % (sum(speed_list)/len(speed_list))
                avg_direction = "%.2f" % (sum(direction_list)/len(direction_list))
                data_dict['time'] = a_last_time
                data_dict['avg_speed'] = avg_speed
                data_dict['avg_direction'] = avg_direction
                adcp_level_data_info = ADCPLevelDataInfo.objects.filter(
                    time__range=(
                        a_last_time + timedelta(minutes=-10), a_last_time + timedelta(minutes=10))
                ).last()

                if adcp_level_data_info:
                    data_dict['level'] = adcp_level_data_info.level
                    data_dict['power'] = adcp_level_data_info.power
                else:
                    data_dict['level'] = ''
                    data_dict['power'] = ''

            # print(data_dict)
            data_info.append(data_dict)
        print(data_info)
        return render(request, 'data_info.html', {
            "data_info": data_info,
            "station_name": station_name,
        })
