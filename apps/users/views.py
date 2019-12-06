# -*- coding: utf-8 -*-
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from rest_framework.views import APIView
from .forms import RegisterForm, LoginForm, UploadImageForm, UserInfoForm, PasswordForm, CompanySerializer, \
    UserProfileSerializer, MessageSerializer, SystemSettingsForm
from .models import UserProfile, HistoryRecord, Message, CompanyModel, SystemSettings
from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record, make_message, jpush_function_extra
from django.core.urlresolvers import reverse
from devices.models import DevicesInfo
from station.models import StationInfo

DEFAULT_PASSWORD = "123456"


class RegisterView2(LoginRequiredMixin, View):

    def get(self, request):
        register_form = RegisterForm()
        username = request.user
        if str(username) == "AnonymousUser":
            # return HttpResponseRedirect(reverse("login"))
            return render(request, 'register2.html', {'msg': '请先登录确认权限后再注册其他账号'})
        user = UserProfile.objects.get(username=username)
        # print(user.permission)
        if user.permission == 'superadmin':
            company_id = CompanyModel.objects.all()
            return render(request, 'register2.html', {
                'register_form': register_form,
                'permission': user.permission,
                "company_id": company_id
            })
        elif user.permission == 'admin':
            company_id = user.company.id
            return render(request, 'register2.html', {
                'register_form': register_form,
                'permission': user.permission,
                "company_id": company_id
            })
        else:
            company_id = user.company.id
            return render(request, 'register2.html', {
                'permission': user.permission,
                'msg': '您没有权限注册其他账号，请联系管理员',
                "company_id": company_id
            })

    def post(self, request):
        username = request.user.username
        user = UserProfile.objects.get(username=username)
        # print(user.permission)
        if (user.permission != "superadmin") and (user.permission != "admin"):
            return JsonResponse({
                'status': "fail",
                'msg': '您没有权限注册其他账号'
            })
        password = request.POST.get('password', '')
        if password == "":
            password = '123456'
        # print(password)
        permission = request.POST.get('permission', 'user')
        company_id = request.POST.get('company', '')
        username = request.POST.get('username', '')
        if not username or UserProfile.objects.filter(username=username):
            return JsonResponse({
                'status': "fail",
                'msg': '请检查用户名是否填写或重复'
            })
        if permission == "superadmin":
            return JsonResponse({
                'status': "fail",
                'msg': '您没有权限注册超级管理员'
            })
        if permission == "admin" and user.permission != "superadmin":
            return JsonResponse({
                'status': "fail",
                'msg': '您没有权限注册管理员'
            })
        user_profile = UserProfile()
        user_profile.username = username
        user_profile.password = make_password(password)
        user_profile.permission = permission
        user_profile.company_id = company_id
        user_profile.save()
        # 记录操作
        if permission == "superadmin":
            permission = "超级管理员"
        elif permission == "admin":
            permission = "管理员"
        elif permission == "user":
            permission = "用户"
        elif permission == "other":
            permission = "其他类型用户"
        make_message(username, "初始密码过于简单，请立即修改密码！", -1)
        create_history_record(user, "注册 %s 账号 %s" % (permission, username))
        return JsonResponse({
            'status': "success",
            'msg': '注册成功'
        })


class LoginView(View):

    def get(self, request):
        # print(request.COOKIES)
        if 'username' in request.COOKIES:
            # 获取记住的用户名
            username = request.COOKIES['username']
        else:
            username = ''
        if 'password' in request.COOKIES:
            # 获取记住的用户名
            password = request.COOKIES['password']
        else:
            password = ''
        return render(request, "login.html", {'username': username, "password": password})

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get('username', '')
            pass_word = request.POST.get('password', '')
            remember = request.POST.get('remember', '')
            # print(remember)
            user = authenticate(username=user_name, password=pass_word)
            if user is not None:
                if user.is_active:
                    response = HttpResponseRedirect(reverse("index"))
                    login(request, user)
                    create_history_record(user, "登录")
                    if remember == "on":
                        # 设置cookie username *过期时间为1周
                        response.set_cookie('username', user_name, max_age=7 * 24 * 3600)
                        response.set_cookie('password', pass_word, max_age=7 * 24 * 3600)
                        response.set_cookie('password', pass_word, max_age=7 * 24 * 3600)
                    return response
                    # return HttpResponse('登录成功')
                else:
                    return render(request, 'login.html', {'msg': "用户未激活"})
            else:
                return render(request, 'login.html', {'msg': '用户名或密码错误！'})
        else:
            return render(request, 'login.html', {'login_form': login_form})


class AppLoginView(View):

    def post(self, request):
        try:
            user_name = request.POST.get('username', '')
            pass_word = request.POST.get('password', '')
            user = authenticate(username=user_name, password=pass_word)
            # print(user_name)
            # print(pass_word)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    create_history_record(user, "app登录")
                    return JsonResponse({
                        "error_no": 0
                    })
                else:
                    return JsonResponse({
                        "error_no": 3,
                        "info": "not active"
                    })
            else:
                return JsonResponse({
                    "error_no": 2,
                    "info": "username or password wrong"
                })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


# 修改密码
class ChangePassword(View):
    def get(self, request):
        return render(request, 'change_password.html', {})

    def post(self, request):
        password_form = PasswordForm(request.POST)
        # print(request.POST)
        if password_form.is_valid():
            old_password = request.POST.get('old_password', '')
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            user = authenticate(username=request.user.username, password=old_password)
            # print(user)
            if not user:
                return render(request, 'change_password.html', {'msg': '请先登录后，再修改密码'})
            if user is not None:
                if password1 == password2:
                    userinfo = UserProfile.objects.get(username=user)
                    userinfo.password = make_password(password1)
                    userinfo.save()
                    create_history_record(user, "修改密码")
                    return render(request, 'change_password.html', {'msg': '密码修改成功！'})
                else:
                    return render(request, 'change_password.html', {'msg': '两次密码不一致'})
            else:
                return render(request, 'change_password.html', {'msg': '原密码错误'})
        else:
            return render(request, 'change_password.html', {'password_form': password_form})


# class AppChangePassword(View):
#
#     def post(self, request):
#         try:
#             username = request.POST.get('username', '')
#             old_password = request.POST.get('old_password', '')
#             password1 = request.POST.get('password1', '')
#             password2 = request.POST.get('password2', '')
#             # print(username)
#             # print(old_password)
#             user = authenticate(username=username, password=old_password)
#             print(user)
#             if not user:
#                 return JsonResponse({
#                     "error_no": 1,
#                     "info": "login first"
#                 })
#             if user is not None:
#                 if password1 == password2:
#                     userinfo = UserProfile.objects.get(username=user)
#                     userinfo.password = make_password(password1)
#                     userinfo.save()
#                     create_history_record(user, "app修改密码")
#                     return JsonResponse({
#                         "error_no": 0
#                     })
#                 else:
#                     return JsonResponse({
#                         "error_no": 1,
#                         "info": "password not same"
#                     })
#             else:
#                 return JsonResponse({
#                     "error_no": 1,
#                     "info": "password wrong"
#                 })
#         except Exception as e:
#             print(e)
#             return JsonResponse({
#                 "error_no": -1,
#                 "info": str(e)
#             })


class ResetPasswordView(View):
    def post(self, request):
        permission = request.user.permission
        if permission not in ['superadmin', 'admin']:
            return JsonResponse({
                "status": "fail",
                "msg": "您没有权限重置密码"
            })
        user_id = request.POST.get('user_id')
        userinfo = UserProfile.objects.get(id=user_id)
        if userinfo.permission == 'admin' and permission == 'admin':
            return JsonResponse({
                "status": "success",
                "msg": "您没有权限重置管理员的密码"
            })
        userinfo.password = make_password("123456")
        userinfo.save()
        make_message(userinfo.username, "已重置密码，请立即修改密码！", -1)
        res = jpush_function_extra(userinfo.username, "2", "已重置密码，请立即修改密码！", "已重置密码，密码过于简单，建议立即修改密码！")
        print(res.json())
        return JsonResponse({
            "status": "success",
            "msg": "重置密码成功"
        })


class LogoutView(View):
    def get(self, request):
        create_history_record(request.user, "退出登录")
        logout(request)
        return HttpResponseRedirect(reverse("login"))
        # return HttpResponse('退出成功')


class LogoutApiView(View):
    def get(self, request):
        # create_history_record(request.user, "退出登录")
        logout(request)
        # return HttpResponseRedirect(reverse("login"))
        # return HttpResponse('退出成功')
        return JsonResponse({
            "error_no": 0
        })


class Index(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'blank.html', {})


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'userinfo.html')

    # 修改用户信息
    def post(self, request):
        userinfo_form = UserInfoForm(request.POST, instance=request.user)
        if userinfo_form.is_valid():
            userinfo_form.save()
            create_history_record(request.user, "修改用户个人信息")
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({
                "status": "fail",
                "errors": userinfo_form.errors,
            })


class UploadImageView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'upload_image.html')

    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)
        if image_form.is_valid():
            image_form.save()
            create_history_record(request.user, "修改头像")
            return HttpResponseRedirect(reverse("user_info"))
        else:
            return HttpResponseRedirect(reverse("upload_image"))


class AllUsersView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        if permission == 'superadmin':
            all_users = UserProfile.objects.all()
        else:
            compan_id = request.user.company.id
            print(compan_id)
            all_users = UserProfile.objects.filter(company_id=compan_id)
        create_history_record(request.user, '查询所有用户信息')
        return render(request, 'all_users.html', {
            "all_users": all_users
        })


class DelUserView(LoginRequiredMixin, View):
    # 删除用户！
    def post(self, request):
        permission = request.user.permission
        # print(permission)
        if permission != 'superadmin':
            return JsonResponse({"status": "fail", "quanxianbuzu": "对不起，您的权限不足！"})
        user_id = request.POST.get("user_id")
        # print(user_id)
        user = UserProfile.objects.get(id=user_id)
        username = user.username
        user.delete()
        create_history_record(request.user, '删除账号 %s' % username)
        return JsonResponse({"status": "success"})


class ChangePermissionView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        permission = request.user.permission
        if permission not in ['superadmin', 'admin']:
            return HttpResponseRedirect(reverse("user_info"))
        user = UserProfile.objects.get(id=user_id)

        return render(request, 'change_permission.html', {
            "user": user
        })

    def post(self, request, user_id):
        permission = request.user.permission
        if permission not in ['superadmin', 'admin']:
            return HttpResponseRedirect(reverse("user_info"))

        user = UserProfile.objects.get(id=user_id)
        # print(request.POST.get('permission'))
        user.permission = request.POST.get('permission')
        user.save()
        username = user.username
        create_history_record(request.user, '修改账号 %s 权限为 %s' % (username, request.POST.get('permission')))
        return JsonResponse({"status": "success"})


class HistoryRecordView(LoginRequiredMixin, View):
    def get(self, request):
        username = request.user.username
        permission = request.user.permission
        if permission == "superadmin":
            all_users = UserProfile.objects.all()[:1500]
            return render(request, 'all_history.html', {
                "all_users": all_users
            })
        history_record = HistoryRecord.objects.filter(username_id=username, r_type=True).order_by('-time')[:1500]
        create_history_record(request.user, '查询历史操作记录')
        return render(request, 'history_record.html', {
            "history_record": history_record
        })


class AllHistoryRecordView(LoginRequiredMixin, View):
    def get(self, request, user_name):
        permission = request.user.permission
        if permission == "superadmin":
            history_record = HistoryRecord.objects.filter(username_id=user_name, r_type=True).order_by('-time')[:1500]
            create_history_record(request.user, '查询 %s 的历史操作记录' % user_name)
            return render(request, 'history_record.html', {
                "history_record": history_record
            })
        return HttpResponseRedirect(reverse("user_info"))


class MessageView(View):

    def get(self, request):
        all_message = Message.objects.filter(username_id=request.user.username)
        return render(request, 'message.html', {
            "all_message": all_message
        })

    def post(self, request):
        msg_id = request.POST.get('msg_id', '')
        # print(msg_id)
        message = Message.objects.get(username_id=request.user.username, id=msg_id)
        message.has_read = True
        message.save()
        return JsonResponse({"status": "success"})


def page_not_found(request):
    # 404
    response = render(request, '404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    # 500
    response = render(request, '500.html', {})
    response.status_code = 500
    return response


class CompanyAddView(LoginRequiredMixin, View):
    """
    新建公司
    """

    def get(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':

            return render(request, 'company_form_add.html')
        else:
            return HttpResponseRedirect(reverse("index"))

    def post(self, request):
        try:
            permission = request.user.permission
            print(permission)
            if permission != "superadmin":
                return JsonResponse({"status": "fail", "errors": "无权限"})
            serializer = CompanySerializer(data=request.POST)
            phone = request.POST["phone"]
            if UserProfile.objects.filter(username=phone).count() > 0:
                return JsonResponse({"status": "fail", "errors": "该电话号码的用户已经存在"})
            if serializer.is_valid():
                newcompany = serializer.save()
                UserProfile.objects.create_user(username=phone, password=DEFAULT_PASSWORD, company=newcompany,
                                                permission="admin")
                create_history_record(request.user, "新建公司%s，管理员%s" % (newcompany.company_name, phone))
                return JsonResponse({"status": "success"})
            return JsonResponse({"status": "fail", "errors": "新建公司失败"})
        except Exception as e:
            print(e)
            return JsonResponse({
                "status": "fail",
                "errors": "公司名称唯一"
            })


class CompanyView(LoginRequiredMixin, View):
    def get(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            all_company = CompanyModel.objects.all().order_by('id')
            all_admin_user = UserProfile.objects.filter(permission='admin')
            return render(request, 'company_info.html', {"all_company": all_company, "all_admin_user": all_admin_user})
        else:
            return HttpResponseRedirect(reverse("index"))


class DelCompanView(LoginRequiredMixin, View):
    def post(self, request):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            try:
                company_id = request.POST.get('company_id', "")
                dev_infos = DevicesInfo.objects.filter(company_id=company_id)
                company = CompanyModel.objects.filter(id=company_id)
                # print(infos)
                if dev_infos:
                    return JsonResponse({"status": "fail", "msg": "该公司下有设备，禁止删除。"})
                company_name = company[0].company_name
                company.delete()
                create_history_record(request.user, '删除公司 %s' % company_name)
                return JsonResponse({"status": "success"})
            except Exception as e:
                print(e)
                return JsonResponse({"status": "fail", "msg": str(e)})
        else:
            return HttpResponseRedirect(reverse("index"))


# 1104重写app html api json

class LoginApiView(APIView):
    """
    登录
    """

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # is_active是否启用
                if user.is_active:
                    login(request, user)
                    create_history_record(user, "app登录")
                    permission = user.permission
                    company_id = user.company
                    company_name = user.company
                    if company_id:
                        company_id = company_id.id
                    else:
                        company_id = ""
                    if company_name:
                        company_name = company_name.company_name
                    else:
                        company_name = ""
                    return JsonResponse({
                        "permission": permission, "company_id": company_id, "error_no": 0,
                        "company_name": company_name
                    })
                else:
                    return JsonResponse({
                        "error_no": 3,
                        "info": "not active"
                    })
            else:
                return JsonResponse({
                    "error_no": -3,
                    "info": "username or password wrong"
                })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class ResetPasswordApiView(APIView):
    """
    共用重置密码
    """

    def post(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")

            user_id = request.data.get('user_id')
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            if permission not in ['superadmin', 'admin']:
                return JsonResponse({
                    "error_no": 2,
                    "info": "您没有权限重置密码"
                })
            if permission == 'superadmin':

                userinfo = UserProfile.objects.get(id=user_id)
                userinfo.password = make_password("123456")
                userinfo.save()
                create_history_record(username, '重置%s的密码' % userinfo.username)
                make_message(userinfo.username, "已重置密码，请立即修改密码！", -1)
            elif permission == 'admin':
                company_id = user.company_id
                userinfo = UserProfile.objects.get(id=user_id, company_id=company_id)
                if userinfo.permission == 'admin' or userinfo.permission == 'superadmin':
                    return JsonResponse({
                        "error_no": -2,
                        "info": "您没有权限重置密码"
                    })

            return JsonResponse({
                "error_no": 0,
                "info": "重置密码成功"
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class ChangePasswordApiView(APIView):
    """
    共用修改密码api
    """

    def post(self, request):
        try:
            username = request.data.get('username', '')
            old_password = request.data.get('old_password', '')
            password1 = request.data.get('password1', '')
            password2 = request.data.get('password2', '')
            user = authenticate(username=username, password=old_password)
            if user is not None:
                if password1 == password2:
                    userinfo = UserProfile.objects.get(username=user)
                    userinfo.password = make_password(password1)
                    userinfo.save()
                    create_history_record(user, "修改密码")
                    return JsonResponse({
                        "error_no": 0,
                        "info": "Success"
                    })
                else:
                    return JsonResponse({
                        "error_no": 1,
                        "info": "两次密码不一致"
                    })
            else:
                return JsonResponse({
                    "error_no": 1,
                    "info": "用户名或密码错误"
                })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class UserInfoApiView(APIView):
    """
    共用用户信息 增删改查
    超级管理员操作所有用户
    管理员仅能操作当前公司下的用户
    """

    def get(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            print(username)
            users = UserProfile.objects.get(username=username)
            permission = users.permission
            if permission == 'superadmin':
                all_users = UserProfile.objects.all().order_by('company_id')
                serializer = UserProfileSerializer(all_users, many=True)
            elif permission == 'admin':
                company_id = users.company_id
                all_users = UserProfile.objects.filter(company_id=company_id).order_by('id')
                serializer = UserProfileSerializer(all_users, many=True)
            else:
                return JsonResponse({"error_no": 2, "info": "你没有权限修改"})
            data = {
                "data": serializer.data,
                "error_no": 0
            }
            create_history_record(username, "查询用户列表")
            return JsonResponse(data)
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def post(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            newusername = request.data.get("newuser")
            phone = request.data.get("phone")
            password = request.data.get("password")
            if not password:
                password = '123456'
            company_name = request.data.get("company_name")
            perm = request.data.get("permission")

            user = UserProfile.objects.get(username=username)
            permission = user.permission

            if permission == 'superadmin':
                company_id = CompanyModel.objects.get(company_name=company_name).id
                UserProfile.objects.create_user(username=newusername, password=password, mobile=phone,
                                                company_id=company_id, permission=perm)
            elif permission == 'admin':
                company_id = user.company_id
                UserProfile.objects.create_user(username=newusername, password=password, mobile=phone,
                                                company_id=company_id, permission=perm)
            else:
                return JsonResponse({"error_no": -2, "info": "没有权限新增用户"})
            create_history_record(username,
                                  "新增用户%s-%s" % (CompanyModel.objects.get(id=company_id).company_name, newusername))
            return JsonResponse({"error_no": 0, "info": "Success"})
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except CompanyModel.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个公司"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def put(self, request):
        """
        仅修改权限
        """
        try:
            username = request.META.get("HTTP_USERNAME")
            perm = request.data.get("permission")
            modify_username = request.data.get("username")
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            if perm == 'superadmin':
                return JsonResponse({"error_no": -2, "info": "你没有权限修改"})

            if permission == 'superadmin':
                modify_user = UserProfile.objects.get(username=modify_username)
                modify_user.permission = perm
                modify_user.save()
                create_history_record(username,
                                      "修改用户%s权限为%s" % (modify_user.username, modify_user.get_permission_display()))
                return JsonResponse({"error_no": 0, "info": "Success"})
            elif permission == 'admin':
                company_id = user.company.id
                modify_user = UserProfile.objects.get(username=modify_username, company_id=company_id)
                modify_user.permission = perm
                modify_user.save()
                create_history_record(username,
                                      "修改用户%s权限为%s" % (modify_user.username, modify_user.get_permission_display()))
                return JsonResponse({"error_no": 0, "info": "Success"})
            else:
                return JsonResponse({"error_no": -2, "info": "你没有权限修改"})

        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def delete(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            delete_username = request.data.get("username")
            admin_user = UserProfile.objects.get(username=username)
            del_user = UserProfile.objects.get(username=delete_username)
            admin_permission = admin_user.permission
            del_user_permission = del_user.permission
            if admin_permission == "superadmin" and (
                    del_user_permission != 'admin' or del_user_permission != 'superadmin'):
                del_user.delete()
                create_history_record(username, "删除用户" + delete_username)
                return JsonResponse({"error_no": 0, "info": "Success"})
            elif admin_permission == 'admin':
                company_id = admin_user.company.id
                del_user = UserProfile.objects.get(username=delete_username, company_id=company_id)
                if del_user and del_user.permission != 'admin':
                    del_user.delete()
                    create_history_record(username, "删除用户" + delete_username)
                    return JsonResponse({"error_no": 0, "info": "Success"})
                else:
                    return JsonResponse({"error_no": -3, "info": "该公司下没有此用户，或权限不足"})
            else:
                return JsonResponse({"error_no": -3, "info": "权限不足"})

        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class CompanyApiView(APIView):
    """
    共用公司管理等
    仅超级管理员
    """

    def get(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            data = list()
            if permission == 'superadmin':
                all_company = CompanyModel.objects.all().order_by('id')
                for company in all_company:
                    admin_user = UserProfile.objects.filter(company=company)
                    admin = [u.username for u in admin_user]
                    data.append({
                        "id": company.id,
                        "company_name": company.company_name,
                        "contact": company.contact,
                        "phone": company.phone,
                        "status": company.company_status,
                        "admin": admin
                    })
                create_history_record(username, "查询所有公司")
                return JsonResponse({
                    "data": data,
                    "error_no": 0
                })
            else:
                return JsonResponse({"error_no": -2, "info": "你没有权限"})

        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def post(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            if permission != "superadmin":
                return JsonResponse({"error_no": -2, "info": "无权限"})
            serializer = CompanySerializer(data=request.data)
            phone = request.data["phone"]
            if UserProfile.objects.filter(username=phone).count() > 0:
                return JsonResponse({"error_no": -3, "info": "该电话号码的用户已经存在"})
            if serializer.is_valid():
                newcompany = serializer.save()
                UserProfile.objects.create_user(username=phone, password=DEFAULT_PASSWORD, company=newcompany,
                                                permission="admin")
                create_history_record(username, "新建公司%s，管理员%s" % (newcompany.company_name, phone))
                return JsonResponse({"error_no": 0, "info": "Success"})
            return JsonResponse({"error_no": -2, "info": "新建公司失败"})
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def put(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            if permission != "superadmin":
                return JsonResponse({"error_no": -2, "info": "无权限"})
            company_id = request.data.get("company_id")
            company_name = request.data.get("company_name")
            company_status = request.data.get("company_status")
            contact = request.data.get("contact")
            phone = request.data.get("phone")
            company = CompanyModel.objects.get(id=company_id)
            company.company_name = company_name
            company.contact = contact
            company.phone = phone
            company.company_status = company_status
            company.save()
            create_history_record(username, "修改公司" + company.company_name)
            return JsonResponse({"error_no": 0, "info": "Success"})
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except CompanyModel.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个公司"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def delete(self, request):
        try:
            print('companyApi del')
            username = request.META.get("HTTP_USERNAME")
            user = UserProfile.objects.get(username=username)
            permission = user.permission
            if permission != "superadmin":
                return JsonResponse({"error_no": -2, "info": "无权限"})
            company_id = request.data['company_id']
            company = CompanyModel.objects.get(id=company_id)
            company.delete()
            user = UserProfile.objects.filter(company=company_id)
            user.delete()
            create_history_record(username, "删除公司%s，用户%s" % (company.company_name, [u.username for u in user]))
            return JsonResponse({"error_no": 0, "info": "Success"})
        except CompanyModel.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个公司"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class MessageApiView(APIView):

    def get(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            all_message = Message.objects.filter(username__username=username)
            message_ser = MessageSerializer(all_message, many=True)

            return JsonResponse({
                "error_no": 0,
                "info": "Success",
                "data": message_ser.data
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个用户"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })

    def post(self, request):
        try:
            username = request.META.get("HTTP_USERNAME")
            msg_id = request.data.get('msg_id')
            all_read = request.data.get('all_read')
            if all_read == "1" and not msg_id:
                Message.objects.filter(username__username=username).update(has_read=True)
            else:
                message = Message.objects.get(username__username=username, id=msg_id)
                message.has_read = True
                message.save()
            return JsonResponse({
                "error_no": 0
            })
        except Message.DoesNotExist:
            return JsonResponse({
                "error_no": -2,
                "info": "没有这个消息"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "error_no": -1,
                "info": str(e)
            })


class SystemStationView(LoginRequiredMixin, View):
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
        create_history_record(request.user, '系统设置查询所有测站点')
        return render(request, 'sys_station.html', {
            "all_station": all_station,
        })


# TODO 目前为全局设置，以后会绑定到站点上
class SystemSettingsView(LoginRequiredMixin, View):
    def get(self, request, station_id):
        permission = request.user.permission
        print(permission)
        if permission == 'superadmin':
            try:
                sys_settings = SystemSettings.objects.get(station_id=station_id)
            except SystemSettings.DoesNotExist:
                sys_settings = SystemSettings.objects.create(station_id=station_id, water_min_level=0,
                                                             water_max_level=0, flow_min_level=0, flow_max_level=0,
                                                             deviate_value=0, volt_value=0, is_alarm=0)
                return render(request, 'sys_settings.html', {"sys_settings": sys_settings})
            return render(request, 'sys_settings.html', {"sys_settings": sys_settings})
        else:
            try:
                company = request.user.company.company_name
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('sys_station'))
            if company and StationInfo.objects.filter(id=station_id, company__company_name=company):
                try:
                    sys_settings = SystemSettings.objects.get(station_id=station_id,
                                                              station__company__company_name=company)
                except SystemSettings.DoesNotExist:
                    sys_settings = SystemSettings.objects.create(station_id=station_id, water_min_level=0,
                                                                 water_max_level=0, flow_min_level=0, flow_max_level=0,
                                                                 deviate_value=0, volt_value=0, is_alarm=0)
                return render(request, 'sys_settings.html', {"sys_settings": sys_settings})
            else:
                return HttpResponseRedirect(reverse('sys_station'))

    def post(self, request, station_id):
        sys_id = request.POST.get('sys_id')
        print(sys_id)
        if sys_id:
            sys_settings = SystemSettings.objects.get(id=sys_id)
            settings_form = SystemSettingsForm(request.POST, instance=sys_settings)
            if settings_form.is_valid():
                settings_form.save()
                create_history_record(request.user, "修改系统设置")
                return JsonResponse({"status": "success", "msg": "修改设置成功"})
            else:
                print(settings_form.errors)
                return JsonResponse({
                    "status": "fail",
                    "msg": "修改设置成功",
                })
        else:
            settings_form = SystemSettingsForm(request.POST)
            if settings_form.is_valid():
                settings_form.save()
                create_history_record(request.user, "设置系统设置")
                return JsonResponse({"status": "success", "msg": "设置成功"})
            else:
                print(settings_form.errors)
                return JsonResponse({
                    "status": "fail",
                    "msg": "设置失败",
                })
