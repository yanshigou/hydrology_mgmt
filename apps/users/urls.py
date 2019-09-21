# -*- coding: utf-8 -*-
__author__ = "dzt"
__date__ = "2019/9/20"
from django.conf.urls import url
from .views import LoginView, LogoutView, UserInfoView, ChangePassword, UploadImageView
from .views import AllUsersView, ChangePermissionView, DelUserView, HistoryRecordView, AllHistoryRecordView
from .views import RegisterView2, ResetPasswordView, MessageView


urlpatterns = [
    url(r'^register/$', RegisterView2.as_view(), name='register'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^userInfo/$', UserInfoView.as_view(), name='user_info'),
    url(r'^changePassword/$', ChangePassword.as_view(), name='change_password'),
    url(r'^resetPassword/$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^uploadImage/$', UploadImageView.as_view(), name='upload_image'),
    url(r'^allUsers/$', AllUsersView.as_view(), name='all_users'),
    url(r'^delUser/$', DelUserView.as_view(), name='del_user'),
    url(r'^changePermission/(?P<user_id>\d+)/$', ChangePermissionView.as_view(), name='change_permission'),
    url(r'^historyRecord/$', HistoryRecordView.as_view(), name='history_record'),
    url(r'^allHistoryRecord/(?P<user_name>.*)/$', AllHistoryRecordView.as_view(), name='aLL_history_record'),
    url(r'^message/$', MessageView.as_view(), name='message'),
]