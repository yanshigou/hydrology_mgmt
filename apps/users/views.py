# -*- coding: utf-8 -*-
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from .forms import RegisterForm, LoginForm, UploadImageForm, UserInfoForm, PasswordForm
from .models import UserProfile, HistoryRecord, Message
from myutils.mixin_utils import LoginRequiredMixin
from myutils.utils import create_history_record, make_message
from django.core.urlresolvers import reverse
from datetime import datetime, timedelta
from django.db.models import Q


class RegisterView2(LoginRequiredMixin, View):

    def get(self, request):
        register_form = RegisterForm()
        username = request.user
        if str(username) == "AnonymousUser":
            # return HttpResponseRedirect(reverse("login"))
            return render(request, 'register2.html', {'msg': '请先登录确认权限后再注册其他账号'})
        user = UserProfile.objects.get(username=username)
        print(user.permission)
        if user.permission == 'superadmin':
            return render(request, 'register2.html', {
                'register_form': register_form,
                'permission': user.permission
            })
        elif user.permission == 'admin':
            return render(request, 'register2.html', {
                'register_form': register_form,
                'permission': user.permission
            })
        else:
            return render(request, 'register2.html', {
                'permission': user.permission,
                'msg': '您没有权限注册其他账号，请联系管理员'
            })

    def post(self, request):
        username = request.user.username
        user = UserProfile.objects.get(username=username)
        print(user.permission)
        if (user.permission != "superadmin") and (user.permission != "admin"):
            return JsonResponse({
                'status': "fail",
                'msg': '您没有权限注册其他账号'
            })
        password = request.POST.get('password', '')
        if password == "":
            password = '123456'
        print(password)
        permission = request.POST.get('permission', 'user')
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
        user_profile.save()
        # 记录操作
        if permission == "superadmin":
            permission = "超级管理员"
        elif permission == "admin":
            permission = "管理员"
        elif permission == "user":
            permission = "普通管理员"
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
        print(request.COOKIES)
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
            print(remember)
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
            print(user)
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


class Index(View):
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
        if permission not in ['superadmin', 'admin']:
            return HttpResponseRedirect(reverse("user_info"))
        all_users = UserProfile.objects.all()
        if permission == 'admin':
            all_users = all_users.exclude(permission='superadmin')
        create_history_record(request.user, '查询所有用户信息')
        return render(request, 'all_users.html', {
            "all_users": all_users
        })


class DelUserView(LoginRequiredMixin, View):
    # 删除用户！
    def post(self, request):
        permission = request.user.permission
        print(permission)
        if permission != 'superadmin':
            return JsonResponse({"status": "fail", "quanxianbuzu": "对不起，您的权限不足！"})
        user_id = request.POST.get("user_id")
        print(user_id)
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
        print(request.POST.get('permission'))
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
        print(msg_id)
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
