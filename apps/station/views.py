from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from hydrology_mgmt.settings import MEDIA_ROOT

from .models import StationInfo, SectionFile
from .forms import StationInfoForm, StationStatusForm
from users.models import CompanyModel
from devices.models import DevicesInfo
from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record


class StationInfoView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            all_station = StationInfo.objects.all()
        else:
            try:
                company = request.user.company.company_name
                # print(company)
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('devices_info'))
            if company:
                all_station = StationInfo.objects.filter(company__company_name=company)
            else:
                all_station = ""
        create_history_record(request.user, '查询所有测站点')
        return render(request, 'station_info.html', {
            "all_station": all_station,
        })


class StationAddView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            company_id = CompanyModel.objects.all()
        else:
            try:
                company_id = request.user.company.id
            except Exception as e:
                print(e)
                return render(request, 'station_info.html', {
                    "all_station": "",
                })
        return render(request, 'station_form_add.html', {"company_id": company_id})

    def post(self, request):
        # print(request.POST)
        station_form = StationInfoForm(request.POST)
        if station_form.is_valid():
            station_form.save()
            return JsonResponse({"status": "success"})

        print(station_form.errors)
        return JsonResponse({
            "status": "fail",
            "errors": "所有信息均为必填"
        })


class StationModifyView(LoginRequiredMixin, View):
    """
    修改测站点
    """

    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        try:
            if permission == 'superadmin':
                station_info = StationInfo.objects.get(id=station_id)
                return render(request, "station_from_modify.html", {
                    "station_info": station_info,
                })
            else:
                try:
                    company_id = request.user.company.id
                    station_info = StationInfo.objects.get(id=station_id, company_id=company_id)
                    return render(request, "station_from_modify.html", {
                        "station_info": station_info,
                    })
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect(reverse('station_info'))
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })

    def post(self, request, station_id):
        try:
            station_info = StationInfo.objects.get(id=station_id)
            station_form = StationInfoForm(request.POST, instance=station_info)
            if station_form.is_valid():
                station_form.save()
                create_history_record(request.user, '修改测站点 %s 的信息' % station_info.station_name)
                return JsonResponse({"status": "success"})
            print(station_form.errors)
            return JsonResponse({
                "status": "fail"
            })
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class StationDelView(LoginRequiredMixin, View):
    """
    删除测站点
    """

    def post(self, request):
        try:
            station_id = request.POST.get('station_id', "")
            devices = DevicesInfo.objects.filter(station_id=station_id)
            if devices:
                return JsonResponse({"status": "fail", "msg": "该测站点下有设备，禁止删除"})
            station = StationInfo.objects.get(id=station_id)
            if station.station_status:
                return JsonResponse({"status": "fail", "msg": "该测站点是有效状态，禁止删除"})

            station_name = station.station_name
            station.delete()
            create_history_record(request.user, '删除测站点 %s' % station_name)
            return JsonResponse({"status": "success"})
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class StationStatusView(LoginRequiredMixin, View):
    """
    修改测站点状态
    """

    def post(self, request):
        try:
            station_id = request.POST.get('id', "")
            station_status = request.POST.get('station_status')
            if station_status == 'true':
                status = "设为有效"
            else:
                status = "设为无效"

            station = StationInfo.objects.get(id=station_id)
            status_form = StationStatusForm(request.POST, instance=station)
            if status_form.is_valid():
                status_form.save()
                station_name = station.station_name
                create_history_record(request.user, '测站点 %s 状态 %s' % (station_name, status))
                return JsonResponse({"status": status + "成功"})
            print(status_form.errors)
            return JsonResponse({"status": status + "失败"})
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            print(e)
            return JsonResponse({
                "status": str(e)
            })


class StationIndexView(LoginRequiredMixin, View):
    """
        测站点主页
    """
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        try:
            if permission == 'superadmin':
                station_info = StationInfo.objects.get(id=station_id)
                return render(request, "station_index.html", {
                    "station_info": station_info,
                })
            else:
                try:
                    company_id = request.user.company.id
                    station_info = StationInfo.objects.get(id=station_id, company_id=company_id)
                    return render(request, "station_index.html", {
                        "station_info": station_info,
                    })
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect(reverse('station_info'))
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })


class StationSectionView(LoginRequiredMixin, View):
    """
        大断面页面
    """
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        try:
            if permission == 'superadmin':
                station_info = StationInfo.objects.get(id=station_id)
                station_file = station_info.section.section
                x_data = list()
                y_data = list()
                if station_file:
                    src = MEDIA_ROOT + "/" + str(station_file)
                    f = open(src)

                    for i in f:
                        line = i.split()
                        if len(line) < 2:
                            continue
                        x = line[0]
                        y = line[1]
                        x_data.append(x)
                        y_data.append(y)
                        # print(x_data, y_data)
                return render(request, "station_section.html", {
                    "station_info": station_info,
                })
            else:
                try:
                    company_id = request.user.company.id
                    station_info = StationInfo.objects.get(id=station_id, company_id=company_id)
                    station_file = station_info.section.section
                    x_data = list()
                    y_data = list()
                    if station_file:
                        src = MEDIA_ROOT + "/" + str(station_file)
                        f = open(src)

                        for i in f:
                            line = i.split()
                            if len(line) < 2:
                                continue
                            x = line[0]
                            y = line[1]
                            x_data.append(x)
                            y_data.append(y)
                            # print(x_data, y_data)
                    return render(request, "station_section.html", {
                        "station_info": station_info,
                        "x_data": x_data,
                        "y_data": y_data,
                    })
                except Exception as e:
                    print(e)
                    return HttpResponseRedirect(reverse('station_info'))
        except StationInfo.DoesNotExist:
            return HttpResponseRedirect(reverse('station_info'))
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
            })

    def post(self, request, station_id):
        try:
            time = request.POST.get('time')
            remarks = request.POST.get('remarks')
            file = request.FILES
            section_file = file.get('section')
            section = SectionFile.objects.create(time=time, section=section_file, remarks=remarks)
            section_id = section.id
            station = StationInfo.objects.get(id=station_id)
            station.section_id = section_id
            station.save()
        except SectionFile.DoesNotExist:
            return JsonResponse({
                "status": "file",
                "msg": "上传文件出错"
            })
        except StationInfo.DoesNotExist:
            return JsonResponse({
                "status": "file",
                "msg": "没有这个测站点"
            })
        return HttpResponseRedirect(reverse('station_section'))
