from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse

from .models import DevicesInfo, StationInfo
from datainfo.models import ADCPDataInfo, ADCPLevelDataInfo
from .forms import DevicesInfoForm, DevicesStatusForm

from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record
from datetime import datetime, timedelta


class DevicesInfoView(LoginRequiredMixin, View):
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            all_devices = DevicesInfo.objects.filter(station_id=station_id)
        else:
            try:
                company = request.user.company.company_name
                # print(company)
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('devices_info'))
            if company:
                all_devices = DevicesInfo.objects.filter(station_id=station_id, station__company__company_name=company)
            else:
                all_devices = DevicesInfo.objects.filter(station_id=station_id, station__company__company_name="")
        try:
            station_name = StationInfo.objects.get(id=station_id).station_name
            create_history_record(request.user, '查询测站点%s所有设备' % station_name)
        except StationInfo.DoesNotExist:
            create_history_record(request.user, '查询测站点所有设备失败，没有这个站点')
        return render(request, 'station_devices.html', {
            "all_devices": all_devices,
            "station_id": station_id
        })


class StationDeviceSelectView(View):
    """
        站点及其设备
    """

    def post(self, request):
        station_id = request.POST.get('station_id')
        if station_id:
            devices = DevicesInfo.objects.filter(station_id=station_id)
        else:
            return JsonResponse({
                "status": "fail"
            })
        device_list = [
            {"id": 0, "name": "断面平均"}
        ]
        for i in devices:
            device_list.append({
                "id": i.id,
                "name": i.name,
            })
        return JsonResponse({
            "devices": device_list
        })


class DeviceAddView(LoginRequiredMixin, View):
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            station = StationInfo.objects.get(id=station_id)
        else:
            try:
                company_id = request.user.company.id
                station = StationInfo.objects.get(company_id=company_id, id=station_id)
            except Exception as e:
                return HttpResponseRedirect(reverse('station_devices', args=[str(station_id)]))
        return render(request, 'device_form_add.html', {"station": station})

    def post(self, request, station_id):
        try:
            device_form = DevicesInfoForm(request.POST)
            if device_form.is_valid():
                device_form.save()
                create_history_record(request.user,
                                      '新增设备 %s %s' % (request.POST.get('device_id'), request.POST.get("name")))
                return JsonResponse({"status": "success"})

            errors = dict(device_form.errors.items())
            return JsonResponse({
                "status": "fail",
                "errors": errors
            })
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class DeviceModifyView(LoginRequiredMixin, View):
    """
    修改设备
    """

    def get(self, request, station_id, device_id):
        permission = request.user.permission
        print(permission)
        try:
            if permission == 'superadmin':
                device_info = DevicesInfo.objects.get(id=device_id)
                return render(request, "device_modify_from.html", {
                    "device_info": device_info,
                    "station_id": station_id
                })
            else:
                try:
                    company_id = request.user.company.id
                    device_info = DevicesInfo.objects.get(id=device_id, station_id=station_id,
                                                          station__company_id=company_id)
                    return render(request, "device_modify_from.html", {
                        "device_info": device_info,
                        "station_id": station_id
                    })
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect(reverse('station_devices', args=[str(station_id)]))
        except DevicesInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_devices', args=[str(station_id)]))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })

    def post(self, request, station_id, device_id):
        try:
            device_info = DevicesInfo.objects.get(id=device_id, station_id=station_id)
            device_form = DevicesInfoForm(request.POST, instance=device_info)
            if device_form.is_valid():
                device_form.save()
                create_history_record(request.user, '修改设备 %s 的信息' % device_info.name)
                return JsonResponse({"status": "success"})
            errors = dict(device_form.errors.items())
            return JsonResponse({
                "status": "fail",
                "errors": errors
            })
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_devices', args=[str(station_id)]))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class StationDelView(LoginRequiredMixin, View):
    """
    删除设备
    """

    def post(self, request):
        station_id = request.POST.get('station_id', "")
        device_id = request.POST.get('device_id', "")
        try:
            device = DevicesInfo.objects.get(id=device_id)
            if device.device_status:
                return JsonResponse({"status": "fail", "msg": "该设备是正常使用状态，禁止删除"})

            device.delete()
            create_history_record(request.user, '删除设备 %s %s' % (device.device_id, device.name))
            return JsonResponse({"status": "success"})
        except DevicesInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_devices', args=[str(station_id)]))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class DeviceStatusView(LoginRequiredMixin, View):
    """
    修改设备状态
    """

    def post(self, request):
        try:
            device_id = request.POST.get('id', "")
            device_status = request.POST.get('device_status')
            if device_status == 'true':
                status = "正常使用"
            else:
                status = "暂停使用"

            device = DevicesInfo.objects.get(id=device_id)
            device_form = DevicesStatusForm(request.POST, instance=device)
            if device_form.is_valid():
                device_form.save()
                device_name = device.name
                create_history_record(request.user, '设备 %s 状态 %s' % (device_name, status))
                return JsonResponse({"status": status + "成功"})
            print(device_form.errors)
            return JsonResponse({"status": status + "失败"})
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            print(e)
            return JsonResponse({
                "status": str(e)
            })


class DeviceDataInfoView(LoginRequiredMixin, View):
    """
    查询单个设备所有数据
    """

    def get(self, request, device_id):
        permission = request.user.permission
        # print(permission)
        end_time = datetime.strptime(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M")[:-1] + "0:00",
                                     "%Y-%m-%d %H:%M:%S")
        start_time = end_time + timedelta(days=-1)
        time_list = list()
        time = start_time

        if permission == 'superadmin':
            device = DevicesInfo.objects.get(id=device_id)
        else:
            company_id = request.user.company.id
            device = DevicesInfo.objects.get(station__company_id=company_id, id=device_id)
        station_id = device.station_id
        data_info = list()
        device_type = device.device_type
        if device_type == "走航式ADCP":
            while True:
                time_list.append(time)
                time = time + timedelta(minutes=10)
                # print(time)
                if time > end_time:
                    break
        if device_type == "水平式ADCP":
            while True:
                time_list.append(time)
                time = time + timedelta(minutes=5)
                # print(time)
                if time > end_time:
                    break
        # print(time_list)
        last_time = time_list[-1]
        # print(last_time)

        adcp_data_infos = ADCPDataInfo.objects.filter(device_id=device.id, time=last_time)
        # print(adcp_data_infos)

        if device_type == "走航式ADCP":
            depth_list = list()
            speed_list = list()
            direction_list = list()
            for adcp_data_info in adcp_data_infos:
                data_dict = dict()
                data_dict['speed'] = adcp_data_info.speed
                data_dict['direction'] = adcp_data_info.direction
                data_dict['depth'] = adcp_data_info.depth
                data_info.append(data_dict)
                depth_list.append(adcp_data_info.depth)
                speed_list.append(adcp_data_info.speed)
                direction_list.append(adcp_data_info.direction)
            # print(data_info)

            return render(request, 'device_data_info.html', {
                "device": device,
                "time_list": time_list,
                "last_time": last_time,
                "depth_list": depth_list,
                "speed_list": speed_list,
                "direction_list": direction_list,
                "station_id": station_id,
                "data_info": data_info,
                "start_time": start_time,
                "end_time": end_time,
            })
        if device_type == "水平式ADCP":
            distance_list = list()
            speed_list = list()
            direction_list = list()
            for adcp_data_info in adcp_data_infos:
                data_dict = dict()
                data_dict['speed'] = adcp_data_info.speed
                data_dict['direction'] = adcp_data_info.direction
                data_dict['distance'] = adcp_data_info.distance
                data_info.append(data_dict)
                distance_list.append(adcp_data_info.distance)
                speed_list.append(adcp_data_info.speed)
                direction_list.append(adcp_data_info.direction)
            # print(data_info)
            return render(request, 'device2_data_info.html', {
                "device": device,
                "time_list": time_list,
                "last_time": last_time,
                "distance_list": distance_list,
                "speed_list": speed_list,
                "direction_list": direction_list,
                "station_id": station_id,
                "data_info": data_info,
                "start_time": start_time,
                "end_time": end_time,
            })

    def post(self, request, device_id):
        permission = request.user.permission
        # print(permission)
        end_time = request.POST.get("end_time")
        start_time = request.POST.get("start_time")
        end_time = datetime.strptime(end_time[:-4] + "0:00", "%Y-%m-%d %H:%M:%S")
        start_time = datetime.strptime(start_time[:-4] + "0:00", "%Y-%m-%d %H:%M:%S")
        time_list = list()
        time = start_time
        if permission == 'superadmin':
            device = DevicesInfo.objects.get(id=device_id)
        else:
            company_id = request.user.company.id
            device = DevicesInfo.objects.get(station__company_id=company_id, id=device_id)
        station_id = device.station_id
        data_info = list()
        device_type = device.device_type

        if device_type == "走航式ADCP":
            while True:
                time_list.append(time)
                time = time + timedelta(minutes=10)
                # print(time)
                if time > end_time:
                    break
        if device_type == "水平式ADCP":
            while True:
                time_list.append(time)
                time = time + timedelta(minutes=5)
                # print(time)
                if time > end_time:
                    break
        # print(time_list)
        # last_time = time_list[-1]
        # print(last_time)

        time = request.POST.get("time")
        # print(time)
        adcp_data_infos = ADCPDataInfo.objects.filter(device_id=device.id, time=time)
        if device_type == "走航式ADCP":
            depth_list = list()
            speed_list = list()
            direction_list = list()
            for adcp_data_info in adcp_data_infos:
                data_dict = dict()
                data_dict['speed'] = adcp_data_info.speed
                data_dict['direction'] = adcp_data_info.direction
                data_dict['depth'] = adcp_data_info.depth
                data_info.append(data_dict)
                depth_list.append(adcp_data_info.depth)
                speed_list.append(adcp_data_info.speed)
                direction_list.append(adcp_data_info.direction)
            # print(data_info)
            return render(request, 'device_data_info.html', {
                "device": device,
                "time_list": time_list,
                "last_time": datetime.strptime(time, "%Y-%m-%d %H:%M:%S"),
                "depth_list": depth_list,
                "speed_list": speed_list,
                "direction_list": direction_list,
                "station_id": station_id,
                "data_info": data_info,
                "start_time": start_time,
                "end_time": end_time,
            })
        if device_type == "水平式ADCP":
            distance_list = list()
            speed_list = list()
            direction_list = list()
            for adcp_data_info in adcp_data_infos:
                data_dict = dict()
                data_dict['speed'] = adcp_data_info.speed
                data_dict['direction'] = adcp_data_info.direction
                data_dict['distance'] = adcp_data_info.distance
                data_info.append(data_dict)
                distance_list.append(adcp_data_info.distance)
                speed_list.append(adcp_data_info.speed)
                direction_list.append(adcp_data_info.direction)
            # print(data_info)
            return render(request, 'device2_data_info.html', {
                "device": device,
                "time_list": time_list,
                "last_time": datetime.strptime(time, "%Y-%m-%d %H:%M:%S"),
                "distance_list": distance_list,
                "speed_list": speed_list,
                "direction_list": direction_list,
                "station_id": station_id,
                "data_info": data_info,
                "start_time": start_time,
                "end_time": end_time,
            })
