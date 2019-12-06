from django.db import models
from devices.models import DevicesInfo
from station.models import StationInfo


class ADCPDataInfo(models.Model):
    device = models.ForeignKey(DevicesInfo, verbose_name="仪器")
    time = models.DateTimeField(verbose_name="时间")
    speed = models.CharField(max_length=10, verbose_name='流速')
    direction = models.CharField(max_length=10, verbose_name='流向')
    depth = models.CharField(max_length=10, verbose_name="走航式-水深", null=True, blank=True)
    distance = models.CharField(max_length=10, verbose_name="水平式-距离", null=True, blank=True)

    class Meta:
        verbose_name = 'ADCP测量信息表'
        verbose_name_plural = verbose_name


class ADCPLevelDataInfo(models.Model):
    device = models.ForeignKey(DevicesInfo, verbose_name="仪器")
    time = models.DateTimeField(verbose_name="时间")
    level = models.CharField(max_length=10, verbose_name="水位", null=True, blank=True)
    power = models.CharField(max_length=10, verbose_name="电压", null=True, blank=True)

    class Meta:
        verbose_name = 'ADCP水位信息表'
        verbose_name_plural = verbose_name


class SectionDataInfo(models.Model):
    station = models.ForeignKey(StationInfo, verbose_name="测站点")
    time = models.DateTimeField(verbose_name="时间")
    distance = models.CharField(max_length=10, verbose_name="距离")
    elevation = models.CharField(max_length=10, verbose_name="高程")

    class Meta:
        verbose_name = '大断面信息表'
        verbose_name_plural = verbose_name
