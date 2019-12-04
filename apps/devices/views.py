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
            all_devices = DevicesInfo.objects.all()
        else:
            try:
                company = request.user.company.company_name
                # print(company)
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('devices_info'))
            if company:
                all_devices = DevicesInfo.objects.filter(station_id=station_id)
            else:
                all_devices = ""
        try:
            station_name = StationInfo.objects.get(id=station_id).station_name
        except StationInfo.DoesNotExist:
            create_history_record(request.user, '没有这个测站点')

        create_history_record(request.user, '查询测站点%s所有设备' % station_name)
        return render(request, 'station_devices.html', {
            "all_devices": all_devices,
            "station_id": station_id
        })
