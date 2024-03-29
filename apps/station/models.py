from django.db import models
from users.models import CompanyModel


class SectionFile(models.Model):
    time = models.DateTimeField(verbose_name="实测日期")
    remarks = models.CharField(max_length=200, null=True, blank=True, verbose_name="备注")
    mark_line = models.CharField(max_length=5, verbose_name="水位线")
    section = models.FileField(upload_to="SectionFile/%Y/%m", max_length=100, verbose_name='大断面文件')


class StationInfo(models.Model):
    company = models.ForeignKey(CompanyModel, verbose_name='所属公司')
    station_name = models.CharField(max_length=50, verbose_name="站名")
    station_code = models.CharField(max_length=20, verbose_name="站码")
    river = models.CharField(max_length=20, verbose_name="河流")
    longitude = models.CharField(max_length=30, verbose_name='经度')
    latitude = models.CharField(max_length=30, verbose_name='纬度')
    station_status = models.BooleanField(default=True, verbose_name="是否有效")
    is_normal = models.BooleanField(default=True, verbose_name="是否正常")
    station_address = models.CharField(max_length=200, verbose_name="站点地址")
    section = models.ForeignKey(SectionFile, verbose_name="大断面", null=True, blank=True)

    class Meta:
        verbose_name = '测站点信息'
        verbose_name_plural = verbose_name
