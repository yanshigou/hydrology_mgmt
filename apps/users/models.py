# -*- coding: utf-8 -*-
from django.db import models


# 继承自带的User表 再添加需要的其他字段
from django.contrib.auth.models import AbstractUser


class CompanyModel(models.Model):
    company_name = models.CharField(max_length=50, verbose_name='公司名称', unique=True)
    contact = models.CharField(max_length=50, verbose_name='联系人')
    phone = models.CharField(max_length=50, verbose_name='联系电话', unique=True)
    company_status = models.IntegerField(default=1, verbose_name='公司状态')


class UserProfile(AbstractUser):
    permission_list = (
        ('superadmin', '超级管理员'),
        ('admin', '管理员'),
        ('user', '用户'),
        ('other', '其他用户')
    )
    name = models.CharField(max_length=20, verbose_name='姓名', default='')
    gender = models.CharField(max_length=10, choices=(('male', '男'), ('female', '女')), default='male')
    company = models.ForeignKey(CompanyModel, verbose_name='所属公司', null=True, blank=True)
    unique_id = models.CharField(max_length=18, blank=True, null=True, verbose_name='唯一识别号')
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='联系电话')
    image = models.ImageField(upload_to="image/%Y/%m", default='image/default.png', max_length=100)
    permission = models.CharField(max_length=10, choices=permission_list, default='superadmin', verbose_name="权限")

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def unread_nums(self):
        # 获取用户未读消息的数量
        return Message.objects.filter(username=self.username, has_read=False).count()

    def unread_contents(self):
        # 获取未读消息的详细内容
        return Message.objects.filter(username=self.username, has_read=False)

    def get_company_name(self):
        # 获取公司名称
        if self.company:
            return CompanyModel.objects.get(id=self.company.id).company_name
        else:
            return ""


class HistoryRecord(models.Model):
    username = models.ForeignKey(UserProfile, to_field='username', verbose_name="用户")
    operation_content = models.CharField(max_length=100, verbose_name=u'操作内容')
    time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    r_type = models.BooleanField(default=True, verbose_name="记录类型")

    class Meta:
        verbose_name = '历史操作记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Message(models.Model):
    type_list = (
        (0, "消息"),
        (1, "提醒"),
        (-1, "警告")
    )
    # 默认为0 发送消息给所有用户，其他值为用户id
    username = models.ForeignKey(UserProfile, to_field='username', verbose_name="用户")
    time = models.DateTimeField(auto_now_add=True, verbose_name='时间')
    content = models.CharField(max_length=1024, verbose_name='消息内容')
    m_type = models.IntegerField(choices=type_list, default=0, verbose_name="消息类型")
    has_read = models.BooleanField(default=False, verbose_name='是否已读')

    class Meta:
        verbose_name = '用户消息'
        verbose_name_plural = verbose_name


class SystemSettings(models.Model):
    # TODO 理论上系统设置是绑定站点
    water_min_level = models.CharField(max_length=10, verbose_name="水位坐标最小值")
    water_max_level = models.CharField(max_length=10, verbose_name="水位坐标最大值")
    flow_min_level = models.CharField(max_length=10, verbose_name="流量坐标最小值")
    flow_max_level = models.CharField(max_length=10, verbose_name="流量坐标最大值")
    deviate_value = models.CharField(max_length=10, verbose_name="偏离报警阈值")
    volt_value = models.CharField(max_length=10, verbose_name="电压报警阈值")
    is_alarm = models.BooleanField(default=True, verbose_name="是否报警")

    class Meta:
        verbose_name = '系统设置'
        verbose_name_plural = verbose_name
