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
from myutils.utils import create_history_record, draw_section_image


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
                return HttpResponseRedirect(reverse('index'))
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
        try:
            station_form = StationInfoForm(request.POST)
            if station_form.is_valid():
                station_form.save()
                create_history_record(request.user, '新增测站点 %s %s' % (
                request.POST.get('station_code'), request.POST.get('station_name')))
                return JsonResponse({"status": "success"})

            errors = dict(station_form.errors.items())
            return JsonResponse({
                "status": "fail",
                "errors": errors
            })
        except Exception as e:
            return JsonResponse({
                "status": "fail",
                "msg": str(e)
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
                section = station_info.section
                section_image = ""
                if section:
                    station_file = section.section
                    if station_file:
                        print(station_file.url)
                        section_image = station_file.url.split('.')[0] + ".png"

                return render(request, "station_section.html", {
                    "station_info": station_info,
                    "section_image": section_image
                })
            else:
                try:
                    company_id = request.user.company.id
                    station_info = StationInfo.objects.get(id=station_id, company_id=company_id)
                    section = station_info.section
                    section_image = ""
                    if section:
                        station_file = section.section
                        if station_file:
                            print(station_file.url)
                            section_image = station_file.url.split('.')[0] + ".png"

                    return render(request, "station_section.html", {
                        "station_info": station_info,
                        "section_image": section_image
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
            mark_line = request.POST.get('mark_line')
            file = request.FILES
            section_file = file.get('section')
            section = SectionFile.objects.create(time=time, section=section_file, remarks=remarks, mark_line=mark_line)
            section_id = section.id
            station = StationInfo.objects.get(id=station_id)
            station.section_id = section_id
            station.save()
            file_path = str(section.section)
            file = MEDIA_ROOT + "/" + file_path
            file_name = file.split(".")[0] + ".png"
            if draw_section_image(file, float(mark_line), file_name):
                print(file_name)
                # ajax调用会出现权限不足画图错误
                # return JsonResponse({
                #     "status": "success",
                #     "file_name": file_name
                # })
                return HttpResponseRedirect(reverse('station_section', args=[str(station_id)]))
        except SectionFile.DoesNotExist:
            return JsonResponse({
                "status": "fail",
                "msg": "上传文件出错"
            })
        except StationInfo.DoesNotExist:
            return JsonResponse({
                "status": "fail",
                "msg": "没有这个测站点"
            })
        # ajax调用会出现权限不足画图错误
        return JsonResponse({
            "status": "fail",
            "msg": "画图出错，请检查文件是否正确"
        })


class ShowMapView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        if permission == 'superadmin':
            all_station = StationInfo.objects.filter(station_status=True)
        else:
            try:
                company = request.user.company.company_name
            except Exception as e:
                print(e)
                return JsonResponse({"status": "fail"})
            if company:
                all_station = StationInfo.objects.filter(company__company_name=company, station_status=True)
            else:
                all_station = []
        station_data = list()
        for station in all_station:
            is_normal = station.is_normal
            if is_normal:
                station_type = 1
            else:
                station_type = 0
            station_data.append({
                "station_id": station.id,
                "name": station.station_name,
                "center": str(station.longitude) + "," + str(station.latitude),
                "type": station_type,
            })
        print(station_data)
        return render(request, "map2.html", {"station_data": station_data})

    def post(self, request):
        permission = request.user.permission
        if permission == 'superadmin':
            all_station = StationInfo.objects.filter(station_status=True)
        else:
            try:
                company = request.user.company.company_name
            except Exception as e:
                print(e)
                return JsonResponse({"status": "fail"})
            if company:
                all_station = StationInfo.objects.filter(company__company_name=company, station_status=True)
            else:
                all_station = []
        a = ""
        print(all_station)
        for station in all_station:
            a += str(station.longitude) + ',' + str(station.latitude) + ',' + str(station.station_name) + '\n'

        return JsonResponse({"status": "success", "str_data": a})
