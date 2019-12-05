from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse

from .models import DevicesInfo, StationInfo
from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record


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
                all_devices = ""
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
        print(request.POST)
        station_form = StationInfoForm(request.POST)
        if station_form.is_valid():
            station_form.save()
            return JsonResponse({"status": "success"})

        print(station_form.errors)
        return JsonResponse({
            "status": "fail",
            "errors": "所有信息均为必填"
        })